import pytest
from app import consumer

@pytest.mark.asyncio
async def test_inference_wrapper(monkeypatch):
    monkeypatch.setattr(consumer, "INFERENCE_DELAY_SECONDS", 0)
    assert await consumer.run_inference("hello", "m1") == "Processed: hello by m1"

@pytest.mark.asyncio
async def test_duplicate_message_is_skipped(monkeypatch):
    async def unchanged(*args, **kwargs): return False
    monkeypatch.setattr(consumer.database, "update_status", unchanged)
    assert await consumer.process_message({"request_id": "r1", "input_data": "x"}) is False
