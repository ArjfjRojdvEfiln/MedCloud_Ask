from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

# 密码加密上下文，使用 bcrypt 算法
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """明文密码 → bcrypt 哈希，存数据库的是这个"""
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """登录时验证：用户输入的密码 vs 数据库里的哈希"""
    return pwd_context.verify(plain, hashed)


def create_access_token(payload: dict) -> str:
    """生成 JWT Token"""
    data = payload.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)
    data.update({"exp": expire})
    return jwt.encode(data, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    """解析 JWT Token，失败抛异常"""
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        raise ValueError("Token 无效或已过期")