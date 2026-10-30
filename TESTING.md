# Testing notes

## Environment and commands

- Available system Python: 3.9.6 (below the project's declared Python 3.10+
  support).
- Installed `requirements-dev.txt` in local `.venv`.
- Baseline attempt before edits: `python3 -m pytest -q` could not start because
  pytest was not installed in the system interpreter.
- Post-change command: `.venv/bin/python -m pytest -q`.
- Actual summary: **234 passed in 0.09s**.
- Demo command: `.venv/bin/python -m main`.
- Demo output: `{'order_id': 'O-7', 'partner_id': 'P-2', 'pickup_minutes': 13,
  'eta_minutes': 35, 'reason': 'assigned'}`.
- `git diff --check` completed with no whitespace errors.

The suite passed in the available Python 3.9.6 environment, but this does not
confirm behavior under the required Python 3.10+ runtime.

## Edge-case evidence

| Case / input | Expected behaviour | Actual result | Test evidence |
|---|---|---|---|
| One or both required travel keys absent | Candidate is ineligible; missing duration is not zero | Passed in the 234-test run | `test_missing_travel_is_not_zero`; `test_eta_is_ineligible_when_either_required_route_is_missing` |
| Negative, boolean, non-finite, or non-numeric preparation/travel duration | Reject candidate or order safely | Passed in the 234-test run | `test_invalid_or_missing_travel_time_rejected`; `test_preparation_time_validation` |
| Partner inactive or at capacity | Do not assign that partner | Passed in the 234-test run | `test_inactive_partner_not_assigned`; `test_full_partner_not_assigned`; parametrized acceptance matrices |
| Equal ETA for differently ordered partners | Choose lexicographically smaller partner ID | Passed in the 234-test run | `test_tie_break_by_partner_id`; `test_ties_break_by_partner_id_independent_of_input_order` |
| Duplicate cancellation event | Workload is released once and event ID appears once | Passed in the 234-test run | `test_duplicate_cancellation_is_idempotent`; `test_duplicate_cancellation_is_idempotent_across_workloads` |
| Malformed order, travel container, or active-order list | Return unassigned/ineligible result without raising | Passed in the 234-test run | `test_malformed_order_and_partner_records_are_safe`; `test_malformed_travel_container_is_reported_without_crashing`; `test_invalid_active_order_list_does_not_crash_or_assign` |
| Cancellation state input mapping | Leave caller's partner mapping unchanged | Passed in the 234-test run | `test_cancellation_does_not_mutate_input_partner` |
| Extremely large integer duration | Reject safely instead of raising during finite-value validation | Passed in the 234-test run | `test_unrepresentably_large_time_values_are_rejected_safely` |

## Regression tests added

Added tests for malformed records, invalid travel containers, invalid active
order lists, and cancellation input immutability. Existing tests cover ETA
math, missing routes, validation, capacity boundaries, deterministic ties, and
cancellation idempotency.

## Remaining verification

Repeat the test and demo commands under Python 3.10 or newer. No workflow files
were present in this checkout, so no GitHub Actions result is available.
