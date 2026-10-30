# Approach and implementation decisions

## Baseline

- Before editing, checked the available interpreter and attempted
  `python3 -m pytest -q`.
- The host had Python 3.9.6 and pytest was not installed, so the baseline
  suite could not start. Python 3.9 is also below this repository's declared
  Python 3.10+ support.
- After editing, installed the declared development requirements into a local
  virtual environment and ran the test suite and demo. Results are recorded in
  [`TESTING.md`](TESTING.md).

## Codebase and data flow

`main.py` obtains the synthetic order, partners, and tuple-keyed travel mapping
from `fixtures.py`, then calls `service.assign_order`. `models.py` defines the
dictionary fields. `estimate_eta` calculates a partner-specific pickup and
delivery time. `assign_order` filters candidates, picks the lowest ETA, and
returns a dictionary. `process_cancellation` returns a copied partner record
with workload and active-order state updated.

The starter already used `None` to identify missing route entries and had the
correct ETA expression and tie-break key. Its candidate selection lacked
input, active-status, capacity, and duration checks. Its cancellation helper
recorded event IDs but did not check them before applying a repeated event.

## Implementation strategy

- Kept the repository's dictionary-based models and public function signatures
  so callers and visible tests remain compatible.
- Centralized checks for IDs and finite, non-negative minute values. Invalid
  orders, partners, current times, and travel mappings return safe ineligible
  or unassigned results.
- Filtered inactive and full partners before calculating their ETAs. Missing
  or invalid travel legs stay unknown and disqualify the candidate.
- Kept selection deterministic with `(eta_minutes, partner_id)` ordering.
- Made cancellation idempotent by checking the event ID before mutation,
  recording only valid new IDs, and releasing an order only while it remains
  active. The input mapping is copied before changes.

## Verification and limitations

Added regression cases for malformed records, invalid travel containers, an
invalid active-order list, and cancellation input immutability. The existing
acceptance suite also covers ETA arithmetic, missing travel, capacity,
inactive partners, tie-breaking, and duplicate cancellation. All 234 tests
passed under Python 3.9.6, and `python -m main` produced an assignment with a
35-minute ETA. The tests were not run under a supported Python 3.10+ runtime,
so that compatibility still needs confirmation in such an environment.
