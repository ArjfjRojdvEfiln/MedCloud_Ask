from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine, Base
from app.core.config import settings
from app.api.v1 import auth
from app.models import organization, user

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


@app.get("/health")
async def health():
    return {"status": "ok"}

# 加一个启动事件
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
