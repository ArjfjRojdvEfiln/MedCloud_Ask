from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

# 异步引擎
engine = create_async_engine(
    settings.database_url,
    echo=settings.app_env == "development",  # 开发环境打印 SQL，生产关掉
    pool_size=10,
    max_overflow=20,
)

# Session 工厂
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# 所有 ORM Model 的基类，D3 建表时用
class Base(DeclarativeBase):
    pass


async def get_db():
    """FastAPI 依赖注入用，自动管理 session 生命周期"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise