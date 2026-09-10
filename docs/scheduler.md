# NexPharmAI AI Production Scheduler & Rescheduling

## Scheduler Engine: Google OR-Tools
NexPharmAI utilizes Constraint Programming (CP-SAT solver) to schedule pharmaceutical production orders across compatible machines.

### Constraints Modeled
1. **Machine Availability**: Machines marked as `CRITICAL`, `MAINTENANCE`, or `OFFLINE` are excluded from the scheduling horizon.
2. **Machine Capability / Compatibility**: Batches are only scheduled on machines validated for the product recipe.
3. **No Machine Overlap**: A machine can only process one batch at any given time interval.
4. **Inventory Gating**: If required raw materials are insufficient, the order cannot be scheduled or is flagged with a material block.
5. **Due Dates & Priorities**: Orders are prioritized to minimize tardiness penalties and tardy batch counts.
6. **Maintenance Windows**: Scheduled preventive or predictive maintenance intervals act as hard non-operational blocks.

### Dynamic Automatic Rescheduling
When telemetry or predictive maintenance triggers a machine health status change to `CRITICAL` or `MAINTENANCE`:
1. The system identifies all active and planned batches assigned to the affected machine.
2. A scheduling conflict event is emitted.
3. The dynamic rescheduler searches for alternative eligible machines with adequate capacity.
4. Inventory availability is re-verified for alternative lines.
5. The optimization model reruns with the degraded machine flagged unavailable.
6. A new versioned schedule revision is generated and stored in `schedule_revisions`, preserving the predecessor schedule for compliance audit.
7. Change logs capture the trigger cause (e.g., "Machine M-001 entered critical health state due to elevated failure probability").
