from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.core.database import get_db
from app.core.deps import get_current_user
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
    """更新机构名称"""
    org = await db.get(Organization, current_user.organization_id)
    if not org:
        raise HTTPException(status_code=404, detail="机构不存在")
    org.name = body.name
    # get_db() 自动 commit
    return {"msg": "更新成功", "name": org.name}