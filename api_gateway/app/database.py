from datetime import datetime, timezone
from sqlalchemy import DateTime, String, Text, select
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
async def create_job(request_id, input_data, model_id):
    async with SessionLocal() as session:
        session.add(InferenceJob(request_id=request_id, input_data=input_data, model_id=model_id, status="PENDING")); await session.commit()
async def get_job(request_id):
    async with SessionLocal() as session: return await session.get(InferenceJob, request_id)
async def mark_failed(request_id, error):
    async with SessionLocal() as session:
        job = await session.get(InferenceJob, request_id)
        if job: job.status, job.error_message = "FAILED", error; await session.commit()
async def database_healthy():
    async with engine.connect() as connection: await connection.execute(select(1))
