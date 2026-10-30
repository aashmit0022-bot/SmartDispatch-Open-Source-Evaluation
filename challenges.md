# Challenges and debugging

## Hardest case: cancellation replay

The starter cancellation function appended each event ID but never checked
whether that ID had already been processed. The key regression assertion
requires a duplicate cancellation to leave `processed_cancellation_ids` as
`["C1"]` and workload at zero. The broader parametrized acceptance tests
repeat cancellations across several workload values.

## Investigation and resolution

I traced `process_cancellation` and its caller-facing dictionary state in
`models.py`, then read the idempotency assertions in
`tests/test_contract.py` and `tests/test_acceptance_matrix.py`. The existing
`active_order_ids` check prevented a second workload release for the same
order, but it did not prevent duplicate event IDs from being recorded. The
updated function returns without applying an event already present in
`processed_cancellation_ids`; it also copies the partner mapping so callers'
input state is not mutated.

The regression test `test_cancellation_does_not_mutate_input_partner` confirms
the input and returned state are separate. The contract and parameterized
cancellation tests passed in the local run.

## Environment limitation

The first baseline attempt could not start because the system Python had no
pytest installed. After installing project requirements in a local virtual
environment, the full suite passed, but the only available interpreter was
Python 3.9.6. The repository requires Python 3.10+, so repeat the suite under
the supported version before treating compatibility as confirmed. No CI
workflow files were present in the checkout to provide that additional run.
