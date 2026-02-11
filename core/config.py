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
    MONGODB_URI_SECONDARY: str | None = None
    MONGODB_DB_NAME: str = "doffair"
    MONGODB_DB_NAME_SECONDARY: str = "doffair_dev"

    AZURE_BLOB_CONNECTION_STRING: str
    AZURE_BLOB_CONTAINER: str

    # -------------------------
    # CORS
    # -------------------------
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:4200",
        "http://localhost:8100",
    ]

    # -------------------------
    # Redis & Queue
    # -------------------------
    REDIS_URL: str = "redis://127.0.0.1:6379/0"
    REDIS_QUEUE_NAME: str = "doffair:notifications"

    # -------------------------
    # Notifications
    # -------------------------
    # Email
    EMAIL_PROVIDER: str = "smtp"  # smtp | sendgrid | ses
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@doffair.com"
    SMTP_FROM_NAME: str = "Doffair"
    
    # SMS
    SMS_PROVIDER: str = "2FACTOR"
    TWOFACTOR_API_KEY: str = ""
    TWOFACTOR_OTP_TEMPLATE: str = ""
    
    # WhatsApp
    WHATSAPP_PROVIDER: str = "twilio"  # twilio | gupshup
    WHATSAPP_ACCOUNT_SID: str = ""
    WHATSAPP_AUTH_TOKEN: str = ""
    WHATSAPP_FROM_NUMBER: str = ""
    
    # Notification Settings
    NOTIFICATION_RETRY_MAX: int = 3
    NOTIFICATION_RETRY_DELAY: int = 60  # seconds

    # -------------------------
    # Rate Limiting
    # -------------------------
    MAX_CONTACT_REVEALS_PER_DAY: int = 5

    AZURE_CDN_BASE_URL: str



    class Config:
        env_file = ".env"
        case_sensitive = True


# Singleton settings object
settings = Settings()

