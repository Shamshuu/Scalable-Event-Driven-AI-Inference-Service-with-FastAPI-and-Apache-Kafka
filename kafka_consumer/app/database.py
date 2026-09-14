import asyncio
from datetime import datetime, timezone
from sqlalchemy import DateTime, String, Text
from sqlalchemy.ext.asyncio import AsyncAttrs, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from .config import DATABASE_URL
class Base(AsyncAttrs, DeclarativeBase): pass
class InferenceJob(Base):
    __tablename__ = "inference_jobs"
    request_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    input_data: Mapped[str] = mapped_column(Text, nullable=False)
    model_id: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    output_data: Mapped[str | None] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
async def init_db():
    async with engine.begin() as connection: await connection.run_sync(Base.metadata.create_all)
async def update_status(request_id, state, output_data=None, error_message=None):
    """Retry transactional writes; COMPLETED is terminal, making duplicate events harmless."""
    for attempt in range(4):
        try:
            async with SessionLocal() as session:
                job = await session.get(InferenceJob, request_id)
                if job is None: return False
                if job.status == "COMPLETED": return False
                job.status = state
                if output_data is not None: job.output_data = output_data
                if error_message is not None: job.error_message = error_message
                await session.commit(); return True
        except Exception:
            if attempt == 3: raise
            await asyncio.sleep(0.25 * 2**attempt)
