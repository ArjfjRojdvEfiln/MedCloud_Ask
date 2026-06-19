import redis.asyncio as redis
from app.core.config import settings

# 模块级单例：整个应用共用这一个客户端
# redis.from_url 内部已经维护连接池，不用自己手动建池
redis_client = redis.from_url(
    settings.redis_url,
    encoding="utf-8",
    decode_responses=True,   # 返回 str 而非 bytes，省掉满地的 .decode()
    max_connections=20,
)


# FastAPI 依赖注入用：需要 Redis 的接口写 redis = Depends(get_redis)
async def get_redis() -> redis.Redis:
    return redis_client