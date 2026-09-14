import asyncio, json, logging
from aiohttp import web
from aiokafka import AIOKafkaConsumer
from . import database
from .config import CONSUMER_HEALTH_PORT, INFERENCE_DELAY_SECONDS, KAFKA_BOOTSTRAP_SERVERS, KAFKA_CONSUMER_GROUP_ID, KAFKA_TOPIC_REQUESTS, LOG_LEVEL
from .logging_config import configure_logging
configure_logging(LOG_LEVEL); logger = logging.getLogger(__name__)
async def run_inference(input_data, model_id):
    await asyncio.sleep(INFERENCE_DELAY_SECONDS)
    return f"Processed: {input_data} by {model_id}"
async def process_message(payload):
    request_id = payload["request_id"]
    changed = await database.update_status(request_id, "PROCESSING")
    if not changed:
        logger.info("duplicate or unknown message skipped", extra={"request_id": request_id, "event": "idempotency_skip"}); return False
    try:
        logger.info("inference started", extra={"request_id": request_id, "event": "inference_start"})
        result = await run_inference(payload["input_data"], payload.get("model_id", "default_model"))
        await database.update_status(request_id, "COMPLETED", output_data=result)
        logger.info("inference completed", extra={"request_id": request_id, "event": "inference_complete"}); return True
    except Exception as exc:
        await database.update_status(request_id, "FAILED", error_message=str(exc))
        logger.exception("inference failed", extra={"request_id": request_id, "event": "inference_failure"}); raise
async def consume_forever():
    consumer = AIOKafkaConsumer(KAFKA_TOPIC_REQUESTS, bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS, group_id=KAFKA_CONSUMER_GROUP_ID, enable_auto_commit=False, auto_offset_reset="earliest")
    await consumer.start()
    try:
        async for message in consumer:
            try:
                payload = json.loads(message.value.decode("utf-8"))
                if not {"request_id", "input_data"}.issubset(payload): raise ValueError("missing required fields")
                await process_message(payload)
                await consumer.commit()
            except (ValueError, json.JSONDecodeError, KeyError):
                logger.exception("invalid message discarded", extra={"event": "invalid_message"}); await consumer.commit()
            except Exception:
                # Do not commit transient failures: Kafka redelivers this record.
                logger.exception("message processing failed; will retry", extra={"event": "processing_retry"})
    finally: await consumer.stop()
async def health(_: web.Request): return web.json_response({"status": "ok", "service": "kafka_consumer"})
async def main():
    await database.init_db()
    app = web.Application(); app.router.add_get("/health", health)
    runner = web.AppRunner(app); await runner.setup(); await web.TCPSite(runner, "0.0.0.0", CONSUMER_HEALTH_PORT).start()
    try: await consume_forever()
    finally: await runner.cleanup(); await database.engine.dispose()
if __name__ == "__main__": asyncio.run(main())
