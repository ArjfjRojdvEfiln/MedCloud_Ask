from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User
from app.models.patient import Patient

# FastAPI 内置的 Bearer Token 提取器
# 自动从请求头里拿 Authorization: Bearer <token>
bearer_scheme = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    依赖注入函数：验证 JWT，返回当前登录用户
    在任何接口里加上 Depends(get_current_user) 就自动要求登录
    """
    token = credentials.credentials

    # 1. 解析 token，失败直接抛 401
    try:
        payload = decode_token(token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 无效或已过期",
        )

    # 2. 从 token 里取出 user_id，查数据库
    user_id = int(payload.get("sub"))
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
        )

    return user


async def get_current_patient(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Patient:
    """
    依赖注入函数：验证患者 JWT，返回当前登录患者
    结构仿照 get_current_user，用于需要患者登录的接口
    """
    token = credentials.credentials

    # 1. 解析 token
    try:
        payload = decode_token(token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 无效或已过期",
        )

    # 2. 校验角色：必须是 patient
    if payload.get("role") != "patient":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="此接口仅限患者端访问",
        )

    # 3. 从 token 取出 patient_id，查数据库
    patient_id = int(payload.get("sub"))
    patient = await db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="患者不存在",
        )

    return patient