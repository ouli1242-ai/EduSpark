from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_NAME: str = "EduSpark"
    DEBUG: bool = True

    # Database - MySQL
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = ""
    MYSQL_DB: str = "eduspark"

    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}?charset=utf8mb4"

    # ChromaDB
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8001
    CHROMA_PERSIST_DIR: str = "./storage/chroma"

    # JWT
    JWT_SECRET: str = "eduspark-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # iFlytek Spark
    SPARK_APP_ID: str = ""
    SPARK_API_SECRET: str = ""
    SPARK_API_KEY: str = ""
    SPARK_URL: str = "wss://spark-api.xf-yun.com/v3.5/chat"
    SPARK_HTTP_URL: str = "https://spark-api-open.xf-yun.com/v1/chat/completions"

    # iFlytek Image
    IMAGE_API_KEY: str = ""

    # iFlytek TTS
    TTS_APP_ID: str = ""
    TTS_API_KEY: str = ""

    # SeeDance
    SEEDANCE_API_KEY: str = ""

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
