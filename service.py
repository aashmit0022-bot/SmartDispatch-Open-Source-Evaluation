"""Offline dispatch selection and cancellation helpers."""

from copy import deepcopy
from math import isfinite
from typing import Mapping


def _valid_id(value):
    return isinstance(value, str) and bool(value.strip())


def _valid_minutes(value):
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
        return False
    try:
        return isfinite(value)
    except (OverflowError, TypeError, ValueError):
        return False


def _valid_order(order):
    return (isinstance(order, Mapping)
            and _valid_id(order.get("order_id"))
            and _valid_id(order.get("restaurant_id"))
            and _valid_id(order.get("destination_zone"))
            and _valid_minutes(order.get("prep_minutes")))


def _invalid_estimate(partner_id=None, reason="invalid_input"):
    return {
        "partner_id": partner_id,
        "pickup_minutes": None,
        "eta_minutes": None,
        "eligible": False,
        "reason": reason,
    }


def estimate_eta(order, partner, travel, now=0):
    """Calculate one partner's ETA or mark the partner ineligible.

    Travel is keyed by ``(partner_zone, restaurant_id)`` and
    ``(restaurant_id, destination_zone)``. Missing or malformed routes are
    unknown; they are never replaced with zero.
    """
    if not _valid_order(order):
        return _invalid_estimate(reason="invalid_order")
    if not isinstance(partner, Mapping):
        return _invalid_estimate(reason="malformed_partner")

    partner_id = partner.get("partner_id")
    if not _valid_id(partner_id):
        return _invalid_estimate(partner_id, "invalid_partner_id")
    zone = partner.get("zone")
    if not _valid_id(zone):
        return _invalid_estimate(partner_id, "invalid_partner_zone")
    if not _valid_minutes(now):
        return _invalid_estimate(partner_id, "invalid_current_time")
    if not _valid_minutes(partner.get("workload_minutes", 0)):
        return _invalid_estimate(partner_id, "invalid_workload")
    if not isinstance(travel, Mapping):
        return _invalid_estimate(partner_id, "invalid_travel_data")

    leg1 = travel.get((zone, order["restaurant_id"]))
    leg2 = travel.get((order["restaurant_id"], order["destination_zone"]))
    if not _valid_minutes(leg1) or not _valid_minutes(leg2):
        return _invalid_estimate(partner_id, "missing_or_invalid_travel_time")

    pickup = now + leg1 + partner.get("workload_minutes", 0)
    eta = pickup + order["prep_minutes"] + leg2
    if not _valid_minutes(pickup) or not _valid_minutes(eta):
        return _invalid_estimate(partner_id, "invalid_eta")
    return {
        "partner_id": partner_id,
        "pickup_minutes": pickup,
        "eta_minutes": eta,
        "eligible": True,
        "reason": None,
    }


def _partner_eligibility_reason(partner):
    if not isinstance(partner, Mapping):
        return "malformed_partner"
    if not _valid_id(partner.get("partner_id")):
        return "invalid_partner_id"
    if partner.get("active") is not True:
        return "inactive_or_invalid_status"
    if not _valid_id(partner.get("zone")):
        return "invalid_partner_zone"

    capacity = partner.get("capacity")
    if (not isinstance(capacity, int) or isinstance(capacity, bool)
            or capacity < 1):
        return "invalid_capacity"
    active_order_ids = partner.get("active_order_ids", [])
    if not isinstance(active_order_ids, list):
        return "invalid_active_orders"
    if len(active_order_ids) >= capacity:
        return "at_capacity"
    if not _valid_minutes(partner.get("workload_minutes", 0)):
        return "invalid_workload"
    return None


def assign_order(order, partners, travel, now=0):
    """Assign the order to the eligible partner with the smallest ETA.

    Ties are resolved by ascending lexicographic partner ID. The input
    partner list and dictionaries are not mutated.
    """
    order_id = order.get("order_id") if isinstance(order, Mapping) else None
    if not _valid_order(order):
        return {
            "order_id": order_id, "partner_id": None, "eta_minutes": None,
            "pickup_minutes": None, "reason": "invalid order record",
        }
    if not _valid_minutes(now):
        return {
            "order_id": order_id, "partner_id": None, "eta_minutes": None,
            "pickup_minutes": None, "reason": "invalid current time",
        }
    if not isinstance(partners, (list, tuple)):
        return {
            "order_id": order_id, "partner_id": None, "eta_minutes": None,
            "pickup_minutes": None, "reason": "invalid partner list",
        }
    if not isinstance(travel, Mapping):
        return {
            "order_id": order_id, "partner_id": None, "eta_minutes": None,
            "pickup_minutes": None, "reason": "invalid travel data",
        }

    options = []
    rejected = []
    seen_ids = set()
    for partner in partners:
        reason = _partner_eligibility_reason(partner)
        if reason:
            rejected.append(reason)
            continue
        partner_id = partner["partner_id"]
        if partner_id in seen_ids:
            rejected.append("duplicate_partner_id")
            continue
        seen_ids.add(partner_id)
        estimate = estimate_eta(order, partner, travel, now)
        if estimate["eligible"]:
            options.append(estimate)
        else:
            rejected.append(estimate["reason"])

    if not options:
        if not partners:
            reason = "no partners available"
        elif "at_capacity" in rejected and all(
            item in {"at_capacity", "inactive_or_invalid_status", "invalid_capacity",
                     "invalid_active_orders", "malformed_partner", "invalid_partner_id",
                     "invalid_partner_zone", "invalid_workload", "duplicate_partner_id"}
            for item in rejected
        ):
            reason = "no partner has available capacity"
        else:
            reason = "no eligible partner: missing or invalid travel data"
        return {
            "order_id": order_id, "partner_id": None, "eta_minutes": None,
            "pickup_minutes": None, "reason": reason,
        }

    chosen = min(options, key=lambda item: (item["eta_minutes"], item["partner_id"]))
    return {
        "order_id": order_id,
        "partner_id": chosen["partner_id"],
        "pickup_minutes": chosen["pickup_minutes"],
        "eta_minutes": chosen["eta_minutes"],
        "reason": "assigned",
    }


def process_cancellation(partner, order_id, event_id):
    """Return a copied partner record with a cancellation applied at most once."""
    if not isinstance(partner, Mapping):
        return deepcopy(partner)
    out = deepcopy(dict(partner))
    active_order_ids = out.get("active_order_ids")
    processed_ids = out.get("processed_cancellation_ids")
    minutes_by_order = out.get("minutes_by_order")

    if not isinstance(active_order_ids, list):
        active_order_ids = []
        out["active_order_ids"] = active_order_ids
    if not isinstance(processed_ids, list):
        processed_ids = []
        out["processed_cancellation_ids"] = processed_ids
    if not isinstance(minutes_by_order, Mapping):
        minutes_by_order = {}

    if not _valid_id(event_id) or event_id in processed_ids:
        return out
    processed_ids.append(event_id)

    if not _valid_id(order_id) or order_id not in active_order_ids:
        return out
    active_order_ids.remove(order_id)
    workload = out.get("workload_minutes", 0)
    released = minutes_by_order.get(order_id, 0)
    if not _valid_minutes(workload):
        workload = 0
    if not _valid_minutes(released):
        released = 0
    out["workload_minutes"] = max(0, workload - released)

    if isinstance(minutes_by_order, dict):
        minutes_by_order.pop(order_id, None)
    return out
