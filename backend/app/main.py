from fastapi import FastAPI
from sqlalchemy import select
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine, Base,AsyncSessionLocal
from app.core.config import settings
from app.api.v1 import auth,organizations,public,knowledge as knowledge_api,chat,appointments,articles as articles_api
from app.models.organization import Organization
from app.models import user, knowledge, conversation, appointment, article,patient
from app.core.redis_client import redis_client
from app.core.bloom_filter import org_bloom
from app.api.v1 import patient_auth

app = FastAPI(
    title="医云问 API",
    version="0.1.0",
    docs_url="/docs" if settings.app_env == "development" else None,
)

# 前后端分离必须加，否则前端请求全被浏览器拦截
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境再收紧
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证"])
app.include_router(public.router, prefix="/api/v1/public", tags=["患者端公开接口"])
app.include_router(
    knowledge_api.router,
    prefix="/api/v1/knowledge",
    tags=["知识库管理"]
)

app.include_router(
    chat.router,
    prefix="/api/v1/chat",
    tags=["对话"]
)


app.include_router(
    articles_api.router,
    prefix="/api/v1/articles",
    tags=["文章管理"]
)


app.include_router(
    appointments.router,
    prefix="/api/v1/appointments",
    tags=["预约管理"]
)

app.include_router(
    patient_auth.router,
    prefix="/api/v1/patient",
    tags=["患者端认证"]
)


@app.get("/health")
async def health():
    return {"status": "ok"}


app.include_router(
    organizations.router,
    prefix="/api/v1/organizations",
    tags=["机构管理"]
)

async def rebuild_org_bloom():
    """从 MySQL 拉全部 slug，整体重建布隆过滤器"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Organization.slug))
        slugs = result.scalars().all()
    # 先删旧位图，再重灌：这是"间接删除"已停用机构的办法
    await redis_client.delete(org_bloom.key)
    for slug in slugs:
        await org_bloom.add(slug)
    print(f"[startup] 布隆过滤器重建完成，载入 {len(slugs)} 个机构 slug")


# 加一个启动事件
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    pong = await redis_client.ping()
    print(f"[startup] Redis 连接{'成功' if pong else '失败'}")
    await rebuild_org_bloom()