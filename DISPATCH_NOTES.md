# Dispatch notes

## 1. Worked ETA from the offline demo

The demo supplies order `O-7` for restaurant `R-2` and destination `Z-9` with
10 minutes of preparation time. Partner `P-2` is in zone `Z-1`, has 5 minutes
of current workload, and the known travel durations are 8 minutes from
`Z-1` to `R-2` and 12 minutes from `R-2` to `Z-9`. With `now=0`:

- Pickup offset = `0 + 8 + 5 = 13` minutes.
- Delivery ETA = `13 + 10 + 12 = 35` minutes from now.
- The demo returned partner `P-2` with pickup 13 and ETA 35.

Partner `P-1` has no restaurant-to-customer route in the fixture and is not a
candidate for this order.

## 2. No-eligible-partner example

For an order at `R-2` headed to `Z-9`, provide only the route
`("Z-1", "R-2"): 8` for active partner `P-2`. The required
`("R-2", "Z-9")` entry is missing, so ETA is unknown. The service leaves the
order unassigned with `partner_id=None`, `eta_minutes=None`, and a reason that
identifies missing or invalid travel data. It never substitutes zero.

## 3. Edge cases and evidence

1. **Capacity boundary:** a partner with one active order and capacity one is
   excluded. Verified by `test_full_partner_not_assigned` and the capacity
   matrix in `test_acceptance_matrix.py`.
2. **ETA tie:** partners `A` and `Z` with equal travel estimates choose `A`
   regardless of input ordering. Verified by `test_tie_break_by_partner_id`
   and the parameterized tie tests.
3. **Cancellation replay:** canceling `O1` with event `C1` twice leaves
   workload at zero and records `C1` once. Verified by
   `test_duplicate_cancellation_is_idempotent` and the cancellation matrix.

All cited tests were included in the local run of 234 passing tests under
Python 3.9.6; rerun on Python 3.10+ to confirm the project's supported runtime.

## 4. Assumptions and limitations

- Partner IDs are compared as strings in ascending lexicographic order.
- Workload and travel/preparation durations are finite, non-negative minutes.
- Capacity is the maximum count of entries in `active_order_ids`.
- Cancellation idempotency is tracked in the partner record and is not
  persisted across processes unless the caller persists that record.
- The API assigns one order at a time and does not update partner state after
  assignment; orchestration must record a new assignment separately.
