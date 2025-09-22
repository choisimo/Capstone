import os

class Settings:
    database_url: str = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/osint_db")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    message_broker_url: str = os.getenv("MESSAGE_BROKER_URL", "amqp://guest:guest@localhost/")
    service_name: str = "osint-planning-service"
    log_level: str = "INFO"

settings = Settings()