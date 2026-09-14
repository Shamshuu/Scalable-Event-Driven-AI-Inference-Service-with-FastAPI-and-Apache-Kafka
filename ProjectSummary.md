# Project Summary

This project is an event-driven AI inference service. Its purpose is to accept AI/model requests quickly, process them in the background, and let clients retrieve results later without making the API wait for long-running inference.

A typical flow:

1. A client sends `POST /inference` with `input_data` and an optional `model_id`.
2. The FastAPI gateway validates the request, creates a unique `request_id`, and stores a `PENDING` job in PostgreSQL.
3. The gateway publishes the request to the Kafka `inference_requests` topic and immediately responds with `202 Accepted`.
4. A separate Kafka consumer worker receives the event, changes its state to `PROCESSING`, and simulates AI inference.
5. The worker stores the result in PostgreSQL as `COMPLETED`.
6. The client calls `GET /inference/{request_id}` to see the current status and final output.

## Main functionality

- `POST /inference`
  - Accepts and validates inference input with Pydantic.
  - Generates a UUID request ID.
  - Creates the database record.
  - Publishes the request to Kafka.
  - Returns immediately instead of blocking for inference.

- `GET /inference/{request_id}`
  - Retrieves the request status: `PENDING`, `PROCESSING`, `COMPLETED`, or `FAILED`.
  - Returns the original input, output, timestamps, and errors when applicable.
  - Returns `404` for unknown IDs.

- Background worker
  - Continuously reads Kafka events through a consumer group.
  - Simulates model work asynchronously.
  - Updates the matching PostgreSQL record.
  - Avoids rerunning a job already marked `COMPLETED`, which makes duplicate Kafka delivery safe.

- Health checks
  - Gateway: `GET /health`
  - Worker: `GET http://localhost:8081/health`
  - Useful for Docker, Kubernetes, load balancers, and monitoring tools.

## How the technologies help

| Technology | Role in the project |
|---|---|
| FastAPI | Provides a fast asynchronous HTTP API, automatic validation, OpenAPI docs, and `/docs` Swagger UI. |
| Pydantic | Ensures incoming request data is valid before it enters the system. |
| Apache Kafka | Decouples request intake from model processing. The API can remain responsive even when inference takes time or traffic spikes. |
| Kafka consumer groups | Allow multiple workers to share workload, enabling horizontal scaling. |
| PostgreSQL | Stores job state and inference results durably, so clients can poll results and data survives service restarts. |
| SQLAlchemy async + asyncpg | Performs non-blocking database access suitable for high-concurrency services. |
| Docker | Packages each service with its dependencies so it runs consistently anywhere. |
| Docker Compose | Starts FastAPI, Kafka, Zookeeper, PostgreSQL, and the consumer together with one command. |
| Structured JSON logging | Makes distributed debugging easier by including consistent events and request IDs in logs. |
| Retry with exponential backoff | Handles temporary Kafka or database failures without immediately failing the request or worker. |
| Pytest | Tests API validation, inference behavior, duplicate-message protection, and an optional end-to-end flow. |

The core architectural benefit is scalability: API gateway instances and consumer workers can be scaled independently. If model processing becomes slow, add more Kafka consumer replicas without slowing down the client-facing API.
