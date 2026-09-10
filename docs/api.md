# NexPharmAI API Documentation

## Base URL
`/api/v1`

## API Routers
- `/auth`: User registration, JWT login, token refresh, current user profile.
- `/users`: User administration and RBAC permission assignment.
- `/machines`: Machine catalog, status toggles, telemetry history, line assignment.
- `/readings`: Telemetry stream ingestion, triggers ML scoring and health updates.
- `/predictive-maintenance`: On-demand ML inference and historical model predictions.
- `/anomaly-detection`: Isolation Forest scoring and severity analysis.
- `/maintenance`: Maintenance work orders, priority schedules, completion workflows.
- `/alerts`: Global alert notifications, acknowledgment, and resolution.
- `/products`: Pharmaceutical master formulation and product catalogs.
- `/production`: Production orders, batch execution, and lifecycle progression.
- `/scheduler`: OR-Tools schedule generation, revision history, and conflict detection.
- `/inventory`: Raw materials, lots, stock adjustments, and shortage verification.
- `/quality`: Batch quality prediction and release risk scores.
- `/forecasting`: 7-day, 30-day, and 90-day demand forecasts.
- `/analytics`: OEE metrics, line throughput, downtime root-causes, and failure rates.
- `/assistant`: Context-aware natural language query answering from actual DB records.
