# Scalable Event-Driven AI Inference Service

A production-minded reference implementation of asynchronous AI inference with FastAPI, Apache Kafka, and PostgreSQL. The gateway acknowledges work quickly; independent worker replicas perform the slow inference and persist the final result.

## Architecture

```text
Client -> FastAPI gateway -> PostgreSQL (PENDING) -> Kafka topic
                                                    |
                                                    v
Client <- GET /inference <- PostgreSQL <- Consumer group / inference worker
```

The request ID is the correlation key in every database row, Kafka message, and structured JSON log. Kafka is keyed by request ID and uses idempotent producer settings. The consumer commits an offset only after processing; duplicate delivery is safe because a `COMPLETED` job is terminal and skipped. Database writes and message publication retry with exponential backoff. A broker failure causes the gateway to mark the persisted request `FAILED` and return `503`, avoiding a misleading accepted response.

## Run it

Prerequisites: Docker Engine with Docker Compose v2.

```bash
git clone https://github.com/Shamshuu/Scalable-Event-Driven-AI-Inference-Service-with-FastAPI-and-Apache-Kafka
cd Scalable-Event-Driven-AI-Inference-Service-with-FastAPI-and-Apache-Kafka
cp .env.example .env
docker compose up --build -d
docker compose ps
```

The API is available at `http://localhost:8000`; interactive OpenAPI documentation is at `/docs`. The consumer health endpoint is exposed on `http://localhost:8081/health`.

## API

Submit work — returns immediately with `202 Accepted`:

```bash
curl -X POST http://localhost:8000/inference \
  -H 'Content-Type: application/json' \
  -d '{"input_data":"Classify this support ticket", "model_id":"demo-v1"}'
```

Example response:

```json
{
  "request_id": "95dbcf4e-3a48-47c8-b52f-2bf90cb9f2bf",
  "status": "PENDING",
  "input_data": "Classify this support ticket",
  "output_data": null,
  "error_message": null,
  "created_at": "2026-09-13T00:00:00Z",
  "updated_at": "2026-09-13T00:00:00Z"
}
```

Poll the job (initially `PENDING` or `PROCESSING`, then `COMPLETED`):

```bash
curl http://localhost:8000/inference/95dbcf4e-3a48-47c8-b52f-2bf90cb9f2bf
```

A missing ID returns `404`. Invalid JSON or an empty `input_data` returns `422`. `/health` returns `503` if the gateway database is unavailable.

## Testing

The small unit suites validate request validation, deterministic request-ID behaviour, simulated inference, and the idempotency path. Run them without containers by installing each service's dependencies, or inside the built service images:

```bash
docker compose run --rm api_gateway pytest -q tests
docker compose run --rm kafka_consumer pytest -q tests
```

With the stack already running, execute the opt-in black-box flow (it produces a message, waits for the worker, and retrieves the stored result):

```bash
docker compose run --rm -e RUN_INTEGRATION=1 -e API_BASE_URL=http://api_gateway:8000 api_gateway pytest -q tests/test_integration.py
```

For an end-to-end smoke test, start the stack, submit the request above, wait longer than `INFERENCE_DELAY_SECONDS` (five seconds by default), then GET its returned ID. The response will include `"status":"COMPLETED"` and `"output_data":"Processed: ..."`.

## Configuration and operational notes

All runtime configuration is documented in [`.env.example`](.env.example): Kafka topic/group/broker, Postgres credentials/URL, ports, log level, and simulated duration. Logs are JSON and include `event` and `request_id` wherever a job is known; inspect them with `docker compose logs -f api_gateway kafka_consumer`.

The worker is deliberately stateless: scale it with `docker compose up -d --scale kafka_consumer=3` for partitions and load that justify more consumers. In a production deployment, use a multi-broker Kafka cluster, TLS/SASL credentials, secrets management, migrations, dead-letter topics for malformed records, and an outbox pattern to make database-write/message-publish atomic across services.
