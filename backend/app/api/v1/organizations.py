from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.redis_client import redis_client
from app.models.user import User
from app.models.organization import Organization


router = APIRouter()

class OrgUpdateRequest(BaseModel):
    name: str

@router.get("/me")
async def get_my_org(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的机构信息"""
    org = await db.get(Organization, current_user.organization_id)
    if not org:
        raise HTTPException(status_code=404, detail="机构不存在")
    return {
        "id": org.id,
        "name": org.name,
        "slug": org.slug,
        "is_active": org.is_active,
        "created_at": org.created_at,
    }

@router.patch("/me")
async def update_my_org(
    body: OrgUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    org = await db.get(Organization, current_user.organization_id)
    if not org:
        raise HTTPException(status_code=404, detail="机构不存在")
    org.name = body.name
    await db.commit()   # 先落库
    # 库改成功了，再清缓存——顺序不能反
    cache_key = f"org:slug:{org.slug}"
    await redis_client.delete(cache_key)
    print(f"[cache] 主动清除：{cache_key}")
    return {"msg": "更新成功", "name": org.name}