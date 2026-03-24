from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Maavi AI Copilot Pro"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Database
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/ai_ca_copilot"

    # JWT
    SECRET_KEY: str = "dev-secret-key-change-in-production-min-32-characters"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # OpenAI
    OPENAI_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4o"

    # File Storage
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 50

    # Email
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = "noreply@aicacopilot.com"
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(f"{settings.UPLOAD_DIR}/invoices", exist_ok=True)
os.makedirs(f"{settings.UPLOAD_DIR}/bank_statements", exist_ok=True)
os.makedirs(f"{settings.UPLOAD_DIR}/gst_reports", exist_ok=True)
os.makedirs(f"{settings.UPLOAD_DIR}/financial_statements", exist_ok=True)
os.makedirs(f"{settings.UPLOAD_DIR}/receipts", exist_ok=True)
