from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.core.bloom_filter import org_bloom
from app.models.organization import Organization
from app.models.user import User
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse

router = APIRouter()


@router.post("/register", status_code=201)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # 1. 检查 slug 是否已被占用
    result = await db.execute(
        select(Organization).where(Organization.slug == body.org_slug)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="该机构标识符已被占用")

    # 2. 检查用户名是否已存在
    result = await db.execute(
        select(User).where(User.username == body.username)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户名已存在")

    # 3. 建机构（事务内，失败自动回滚）
    org = Organization(name=body.org_name, slug=body.org_slug)
    db.add(org)
    await db.flush()  # flush 让 org.id 可用，但还没有 commit

    # 4. 建用户，关联机构
    user = User(
        organization_id=org.id,
        username=body.username,
        hashed_password=hash_password(body.password),
    )
    db.add(user)
    # get_db() 会在请求结束时自动 commit
    await org_bloom.add(org.slug)

    return {"msg": "注册成功", "org_id": org.id}


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    # 1. 查用户
    result = await db.execute(
        select(User).where(User.username == body.username)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 2. 验证密码
    if not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 3. 查机构名（用于返回给前端显示）
    org = await db.get(Organization, user.organization_id)

    # 4. 生成 token，payload 里带上关键信息
    token = create_access_token({
        "sub": str(user.id),
        "org_id": user.organization_id,
        "role": user.role,
    })

    return TokenResponse(
        access_token=token,
        org_id=org.id,
        org_name=org.name,
    )


@router.get("/me")
async def me():
    return {"msg": "todo: 接 JWT 验证"}