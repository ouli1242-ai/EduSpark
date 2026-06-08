from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_NAME: str = "EduSpark"
    DEBUG: bool = True

    # Database - MySQL
    DATABASE_URL: str = "mysql+pymysql://root:root@localhost:3306/eduspark?charset=utf8mb4"

    # ChromaDB
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8001
    CHROMA_PERSIST_DIR: str = "./storage/chroma"

    # JWT
    JWT_SECRET: str = "eduspark-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # DeepSeek（兼容 OpenAI 格式）
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_MODEL: str = "deepseek-v4-flash"

    # Storage
    STORAGE_TYPE: str = "local"  # local | oss
    LOCAL_STORAGE_PATH: str = "./storage/files"
    OSS_ACCESS_KEY: str = ""
    OSS_SECRET_KEY: str = ""
    OSS_BUCKET: str = ""
    OSS_ENDPOINT: str = ""

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
