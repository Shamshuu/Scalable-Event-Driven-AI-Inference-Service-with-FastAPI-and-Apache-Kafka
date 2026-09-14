import os

DATABASE_URL = os.getenv("DATABASE_URL") or "postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}".format(
    user=os.getenv("DB_USER", "inference_user"), password=os.getenv("DB_PASSWORD", "change-me"),
    host=os.getenv("DB_HOST", "postgres"), port=os.getenv("DB_PORT", "5432"), name=os.getenv("DB_NAME", "inference_db"))
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC_REQUESTS = os.getenv("KAFKA_TOPIC_REQUESTS", "inference_requests")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
