from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.security import hash_password, verify_password, create_access_token

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
async def login(body: LoginRequest):
    # 移到函数内部，请求来了再算，不在模块加载时执行
    fake_hashed = hash_password("admin123")

    if body.username != "admin":
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    if not verify_password(body.password, fake_hashed):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    token = create_access_token({"sub": body.username, "role": "admin"})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me")
async def me():
    return {"msg": "todo: 接 JWT 验证"}