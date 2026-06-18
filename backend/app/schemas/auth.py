# backend/app/schemas/auth.py
from pydantic import BaseModel, field_validator
import re


class RegisterRequest(BaseModel):
    org_name: str        # 机构名称，如"北京微笑口腔"
    org_slug: str        # 机构唯一标识，如"beijing-smile"
    username: str        # 管理员用户名
    password: str        # 密码

    @field_validator("org_slug")
    @classmethod
    def slug_must_be_valid(cls, v: str) -> str:
        """slug 只允许小写字母、数字、连字符"""
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError("slug 只能包含小写字母、数字和连字符")
        return v

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("密码至少6位")
        return v


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    org_id: int
    org_name: str
