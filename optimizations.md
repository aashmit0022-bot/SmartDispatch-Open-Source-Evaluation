# Optimizations and trade-offs

## Objective

The work focused on correctness and maintainability: avoid computing an ETA
from invalid or missing inputs, avoid considering inactive or full partners,
and make cancellation replay safe. No performance bottleneck was measured.

## Changes

- Candidate checks happen before ETA calculation, so ineligible partners do
  not perform unnecessary route lookups and arithmetic.
- Validation helpers keep the repeated ID and duration rules consistent.
- The cancellation event-ID membership check prevents duplicate event
  application while preserving the simple in-memory data model.
- Candidate selection remains a single `min` over eligible options, with a
  stable two-field key for deterministic ties.

These choices favor direct control flow and readable failure reasons. No speed
or memory improvement was benchmarked, and none is claimed.

## Alternatives and trade-offs

An indexed partner lookup or heap could reduce work for a much larger dispatch
batch, but this API selects one order from the supplied list. Adding those
structures now would add state and synchronization complexity without
measured benefit. A persistent cancellation store would support process
restarts and concurrent events, but persistence is outside this offline
starter's scope; the current helper only provides idempotency within the
partner record passed to it.

## Next steps

Run the suite under Python 3.10+ and, if realistic larger batch workloads are
introduced, benchmark candidate filtering and route lookups before choosing
an index or batch strategy. Persist processed event IDs with an atomic update
if this logic is moved into a multi-process service.
