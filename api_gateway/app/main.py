import logging, uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Request, status
from . import database
from .config import LOG_LEVEL
from .kafka_producer import KafkaPublisher
from .logging_config import configure_logging
from .models import InferenceRequest, InferenceResponse
configure_logging(LOG_LEVEL); logger = logging.getLogger(__name__)
@asynccontextmanager
async def lifespan(app):
    await database.init_db(); app.state.publisher = KafkaPublisher(); await app.state.publisher.start()
    yield
    await app.state.publisher.stop(); await database.engine.dispose()
app = FastAPI(title="Event-Driven AI Inference Gateway", version="1.0.0", lifespan=lifespan)
def serialize(job): return InferenceResponse(request_id=job.request_id, status=job.status, input_data=job.input_data, output_data=job.output_data, error_message=job.error_message, created_at=job.created_at, updated_at=job.updated_at)
@app.post("/inference", response_model=InferenceResponse, status_code=status.HTTP_202_ACCEPTED)
async def submit_inference(request: InferenceRequest, http_request: Request):
    request_id = str(uuid.uuid4()); created = datetime.now(timezone.utc)
    try: await database.create_job(request_id, request.input_data, request.model_id)
    except Exception as exc:
        logger.exception("database write failed", extra={"request_id": request_id}); raise HTTPException(503, "Database unavailable") from exc
    payload = {"request_id": request_id, "input_data": request.input_data, "model_id": request.model_id, "timestamp": created.isoformat()}
    try: await http_request.app.state.publisher.publish(payload)
    except Exception as exc:
        await database.mark_failed(request_id, "Message broker unavailable")
        logger.exception("publish failed", extra={"request_id": request_id}); raise HTTPException(503, "Message broker unavailable; request was not queued") from exc
    job = await database.get_job(request_id); return serialize(job)
@app.get("/inference/{request_id}", response_model=InferenceResponse)
async def get_inference(request_id: str):
    job = await database.get_job(request_id)
    if not job: raise HTTPException(404, "Inference request not found")
    return serialize(job)
@app.get("/health")
async def health(request: Request):
    try:
        await database.database_healthy(); return {"status": "ok", "service": "api_gateway", "kafka_connected": request.app.state.publisher.producer.client is not None}
    except Exception as exc: raise HTTPException(503, "Database unavailable") from exc
