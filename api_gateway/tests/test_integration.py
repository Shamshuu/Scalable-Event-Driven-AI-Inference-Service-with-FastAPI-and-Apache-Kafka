"""Opt-in black-box test for a running Compose stack.

Run from the API container after `docker compose up -d` with
`RUN_INTEGRATION=1 API_BASE_URL=http://api_gateway:8000 pytest -q tests`.
"""
import asyncio
import os
import pytest
import httpx

pytestmark = pytest.mark.skipif(os.getenv("RUN_INTEGRATION") != "1", reason="requires a running Kafka/Postgres Compose stack")

@pytest.mark.asyncio
async def test_submit_process_and_retrieve():
    base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    async with httpx.AsyncClient(base_url=base_url, timeout=20) as client:
        submitted = await client.post("/inference", json={"input_data": "integration input", "model_id": "test-model"})
        assert submitted.status_code == 202
        request_id = submitted.json()["request_id"]
        for _ in range(12):
            result = await client.get(f"/inference/{request_id}")
            assert result.status_code == 200
            if result.json()["status"] == "COMPLETED":
                assert result.json()["output_data"] == "Processed: integration input by test-model"
                return
            await asyncio.sleep(1)
    pytest.fail("worker did not complete inference in 12 seconds")
