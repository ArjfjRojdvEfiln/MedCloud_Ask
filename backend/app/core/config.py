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
    # 微信开放平台 OAuth2
    wechat_app_id: str = ""
    wechat_app_secret: str = ""
    wechat_redirect_uri: str = ""

    # 阿里云 OSS
    oss_access_key_id: str = ""
    oss_access_key_secret: str = ""
    oss_bucket_name: str = ""
    oss_endpoint: str = ""

    # 阿里云 SMS
    sms_sign_name: str = "阿里云短信测试"
    sms_template_code: str = "SMS_154950909"

    # 环境
    app_env: str = "development"
    # Dify
    dify_api_base: str = "https://api.dify.ai/v1"
    dify_api_key: str = ""
    dify_dataset_id: str = ""
    dify_dataset_api_key: str = ""  # 加这行
    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()