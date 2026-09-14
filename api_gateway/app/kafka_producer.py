import asyncio, json, logging
from aiokafka import AIOKafkaProducer
from .config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC_REQUESTS
logger = logging.getLogger(__name__)
class KafkaPublisher:
    def __init__(self): self.producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS, acks="all", enable_idempotence=True)
    async def start(self): await self.producer.start()
    async def stop(self): await self.producer.stop()
    async def publish(self, payload):
        for attempt in range(4):
            try:
                await self.producer.send_and_wait(KAFKA_TOPIC_REQUESTS, json.dumps(payload).encode(), key=payload["request_id"].encode())
                logger.info("inference message published", extra={"request_id": payload["request_id"], "event": "kafka_publish"}); return
            except Exception:
                if attempt == 3: raise
                await asyncio.sleep(0.25 * 2**attempt)
