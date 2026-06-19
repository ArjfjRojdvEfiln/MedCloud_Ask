# app/api/v1/public.py
import json
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis
from app.core.database import get_db
from app.core.bloom_filter import org_bloom
from app.core.redis_client import get_redis
from app.models.organization import Organization

router = APIRouter()

CACHE_TTL = 600  # 10 分钟，单位秒
CACHE_KEY_PREFIX = "org:slug:"


@router.get("/orgs/{slug}")
async def get_org_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db),
    rc: redis.Redis = Depends(get_redis),   # rc = redis client，简短好认
):
    # ── 第一道闸：布隆过滤器 ──
    if not await org_bloom.exists(slug):
        print(f"[bloom] 拦截：{slug}（未查库）")
        raise HTTPException(status_code=404, detail="机构不存在")

    # ── 第二道闸：Redis 缓存 ──
    cache_key = f"{CACHE_KEY_PREFIX}{slug}"
    cached = await rc.get(cache_key)
    if cached:
        print(f"[cache] 命中：{slug}")
        return json.loads(cached)   # 缓存里存的是 JSON 字符串，反序列化返回

    # ── 第三道闸：MySQL 兜底 ──
    print(f"[cache] 未命中，查库：{slug}")
    result = await db.execute(
        select(Organization).where(
            Organization.slug == slug,
            Organization.is_active.is_(True),
        )
    )
    org = result.scalar_one_or_none()
    if org is None:
        raise HTTPException(status_code=404, detail="机构不存在")

    # 回填缓存，下次同样的 slug 直接走第二层
    data = {"slug": org.slug, "name": org.name}
    await rc.set(cache_key, json.dumps(data), ex=CACHE_TTL)
    print(f"[cache] 回填：{slug}，TTL={CACHE_TTL}s")

    return data