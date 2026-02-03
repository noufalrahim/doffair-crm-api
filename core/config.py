from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # -------------------------
    # App
    # -------------------------
    APP_NAME: str = "Doffair API"
    ENVIRONMENT: str = "development"  # development | staging | production
    DEBUG: bool = True

    # -------------------------
    # Server
    # -------------------------
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # -------------------------
    # Security / JWT
    # -------------------------
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    # -------------------------
    # Database (MongoDB)
    # -------------------------
    MONGODB_URI: str
    MONGODB_DB_NAME: str = "doffair"

    AZURE_BLOB_CONNECTION_STRING: str
    AZURE_BLOB_CONTAINER: str

    # -------------------------
    # CORS
    # -------------------------
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:4200",
        "http://localhost:4400"
    ]

    # -------------------------
    # Notifications (Future)
    # -------------------------
    SMS_PROVIDER: str = "mock"
    EMAIL_PROVIDER: str = "mock"

    # -------------------------
    # Rate Limiting (Future)
    # -------------------------
    MAX_CONTACT_REVEALS_PER_DAY: int = 5

    REDIS_BROKER_URL: str = "redis://localhost:6379/0"
    REDIS_BACKEND_URL: str = "redis://localhost:6379/1"

    # SMS Provider
    SMS_PROVIDER: str = "2FACTOR"

    TWOFACTOR_API_KEY: str
    TWOFACTOR_OTP_TEMPLATE: str

    AZURE_CDN_BASE_URL: str



    class Config:
        env_file = ".env"
        case_sensitive = True


# Singleton settings object
settings = Settings()

