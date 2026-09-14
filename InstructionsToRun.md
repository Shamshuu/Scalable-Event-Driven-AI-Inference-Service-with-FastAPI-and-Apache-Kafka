# Instructions to Run

Run these in Git Bash from scratch. Ensure Docker Desktop is running first.

```bash
git clone https://github.com/Shamshuu/Scalable-Event-Driven-AI-Inference-Service-with-FastAPI-and-Apache-Kafka
cd Scalable-Event-Driven-AI-Inference-Service-with-FastAPI-and-Apache-Kafka

cp .env.example .env
docker compose up --build -d
docker compose ps
```

Wait until all services are healthy:

```bash
docker compose logs -f
```

Press `Ctrl+C` to stop following logs. Check both health endpoints:

```bash
curl http://localhost:8000/health
curl http://localhost:8081/health
```

Submit an inference request:

```bash
curl -i -X POST http://localhost:8000/inference \
  -H "Content-Type: application/json" \
  -d "{\"input_data\":\"Classify this support ticket\",\"model_id\":\"demo-v1\"}"
```

You should receive `HTTP/1.1 202 Accepted` and JSON like:

```json
{
  "request_id": "your-generated-id",
  "status": "PENDING"
}
```

To automatically save the generated ID in Git Bash:

```bash
REQUEST_ID=$(curl -s -X POST http://localhost:8000/inference \
  -H "Content-Type: application/json" \
  -d "{\"input_data\":\"Analyze this event-driven architecture\",\"model_id\":\"demo-v1\"}" \
  | sed -n 's/.*"request_id":"\([^"]*\)".*/\1/p')

echo "$REQUEST_ID"
```

Check the request immediately; it will normally be `PENDING` or `PROCESSING`:

```bash
curl http://localhost:8000/inference/$REQUEST_ID
```

Wait for the simulated inference to finish:

```bash
sleep 6
curl http://localhost:8000/inference/$REQUEST_ID
```

Expected completed result:

```json
{
  "request_id": "your-generated-id",
  "status": "COMPLETED",
  "input_data": "Analyze this event-driven architecture",
  "output_data": "Processed: Analyze this event-driven architecture by demo-v1"
}
```

View the gateway and worker's structured logs:

```bash
docker compose logs -f api_gateway kafka_consumer
```

Try validation handling with an invalid empty input:

```bash
curl -i -X POST http://localhost:8000/inference \
  -H "Content-Type: application/json" \
  -d "{\"input_data\":\"\"}"
```

This should return `422 Unprocessable Entity`.

Try an unknown job ID:

```bash
curl -i http://localhost:8000/inference/does-not-exist
```

This should return `404 Not Found`.

Open FastAPI's interactive API documentation in a browser:

```bash
start http://localhost:8000/docs
```

Run the unit tests:

```bash
docker compose run --rm api_gateway pytest -q tests/test_api.py
docker compose run --rm kafka_consumer pytest -q tests/test_consumer.py
```

Run the full end-to-end integration test while the stack is running:

```bash
docker compose run --rm \
  -e RUN_INTEGRATION=1 \
  -e API_BASE_URL=http://api_gateway:8000 \
  api_gateway pytest -q tests/test_integration.py
```

Stop the project when finished:

```bash
docker compose down
```

To also delete the PostgreSQL data volume and start completely fresh next time:

```bash
docker compose down -v
```
