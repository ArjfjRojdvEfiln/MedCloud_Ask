from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # 数据库
    database_url: str
    # Redis
    redis_url: str
    # RabbitMQ
    rabbitmq_url: str
    # Elasticsearch
    es_url: str
    # JWT
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 10080
    # 环境
    app_env: str = "development"

    model_config = SettingsConfigDict(
        # 往上找两层才到根目录的 .env
        env_file="../.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


# 全局单例，别的文件 from app.core.config import settings 就能用
settings = Settings()