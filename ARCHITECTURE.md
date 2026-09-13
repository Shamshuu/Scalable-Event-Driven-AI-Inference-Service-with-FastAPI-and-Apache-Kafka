# Architecture notes

## Request sequence

```mermaid
sequenceDiagram
  participant C as Client
  participant A as API Gateway
  participant D as PostgreSQL
  participant K as Kafka
  participant W as Worker
  C->>A: POST /inference
  A->>D: insert PENDING job
  A->>K: produce request keyed by request_id
  A-->>C: 202 request_id
  K->>W: consume message
  W->>D: set PROCESSING
  W->>W: simulated model inference
  W->>D: set COMPLETED + output
  C->>A: GET /inference/{id}
  A->>D: fetch job
  A-->>C: current state/result
```

## Failure semantics

The service provides at-least-once processing. The producer waits for Kafka acknowledgement; if all retries fail, the created job becomes `FAILED` and the caller receives `503`. The consumer deliberately leaves transiently failed messages uncommitted. Redelivery is harmless because the durable status is checked first and completed jobs are not re-run. Invalid messages are logged and committed to prevent a poison-message loop.
