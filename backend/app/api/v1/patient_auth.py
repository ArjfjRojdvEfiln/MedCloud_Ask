import secrets
import httpx
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.redis_client import redis_client
from app.core.security import create_access_token
from app.core.config import settings
from app.models.patient import Patient
from app.services.sms_service import generate_code

router = APIRouter()

# ── Schemas ──────────────────────────────────────────
class SendCodeRequest(BaseModel):
    phone: str
    institution_id: int

class PatientLoginRequest(BaseModel):
    phone: str
    institution_id: int
    code: str

class PatientTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    patient_id: int
    phone: str
    name: str


# ── 微信 OAuth2 专用 Schemas ─────────────────────────
class WechatAuthUrlResponse(BaseModel):
    auth_url: str
    state: str


class WechatMockLoginRequest(BaseModel):
    openid: str
    institution_id: int


# ── 内部辅助：查或建 Patient + 发 JWT ─────────────────
async def _login_or_register_patient(
    db: AsyncSession,
    phone: str = "",
    wechat_openid: str | None = None,
    institution_id: int = 0,
) -> PatientTokenResponse:
    """统一登录/注册逻辑：按 phone 或 wechat_openid 查找 Patient，找不到则创建"""
    patient = None

    if wechat_openid:
        result = await db.execute(
            select(Patient).where(
                Patient.wechat_openid == wechat_openid,
                Patient.institution_id == institution_id,
            )
        )
        patient = result.scalar_one_or_none()

    if not patient and phone:
        result = await db.execute(
            select(Patient).where(
                Patient.phone == phone,
                Patient.institution_id == institution_id,
            )
        )
        patient = result.scalar_one_or_none()

    if not patient:
        # 第一次登录，自动注册
        # 微信用户无手机号时，用 openid 生成占位 phone，避免 UNIQUE(phone, institution_id) 冲突
        effective_phone = phone if phone else (f"wx_{wechat_openid[:16]}" if wechat_openid else "")
        patient = Patient(
            phone=effective_phone,
            wechat_openid=wechat_openid,
            institution_id=institution_id,
            name="",
        )
        db.add(patient)
        await db.flush()
    elif wechat_openid and not patient.wechat_openid:
        # 老用户（仅有手机号）首次用微信登录 → 补绑 openid
        patient.wechat_openid = wechat_openid
        await db.flush()

    token = create_access_token({
        "sub": str(patient.id),
        "phone": patient.phone,
        "wechat_openid": patient.wechat_openid or "",
        "institution_id": patient.institution_id,
        "role": "patient",
    })

    return PatientTokenResponse(
        access_token=token,
        patient_id=patient.id,
        phone=patient.phone,
        name=patient.name,
    )


# ── 微信 OAuth2：获取授权跳转 URL ──────────────────────
@router.get("/wechat/auth-url", response_model=WechatAuthUrlResponse)
async def wechat_auth_url(
    redirect_uri: str = Query(default="", description="登录成功后跳回的前端地址"),
):
    """返回微信网页授权 URL。前端拿到后 `window.location.href = auth_url` 跳转"""
    state = secrets.token_urlsafe(32)
    # 存 state → Redis，回调时校验防 CSRF
    await redis_client.set(f"wechat_state:{state}", redirect_uri or "/", ex=600)

    if settings.app_env == "development":
        # 开发模式：跳过微信扫码，直接回调 /wechat/callback 带上 mock code
        callback_url = (
            f"{settings.wechat_redirect_uri}"
            f"?code=mock_dev_code_{secrets.token_hex(4)}"
            f"&state={state}"
        )
        return WechatAuthUrlResponse(auth_url=callback_url, state=state)

    # 生产模式：构造微信开放平台 网站应用 扫码授权 URL
    auth_url = (
        "https://open.weixin.qq.com/connect/qrconnect"
        f"?appid={settings.wechat_app_id}"
        f"&redirect_uri={settings.wechat_redirect_uri}"
        f"&response_type=code"
        f"&scope=snsapi_login"
        f"&state={state}"
        "#wechat_redirect"
    )
    return WechatAuthUrlResponse(auth_url=auth_url, state=state)


# ── 微信 OAuth2：回调端点 ─────────────────────────────
@router.get("/wechat/callback")
async def wechat_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """微信授权后回调此地址，用 code 换 openid，完成登录"""
    # 1. 校验 state（防 CSRF）
    redirect_uri = await redis_client.get(f"wechat_state:{state}")
    if not redirect_uri:
        raise HTTPException(status_code=400, detail="state 无效或已过期")
    await redis_client.delete(f"wechat_state:{state}")

    # 2. 用 code 换 access_token + openid
    if settings.app_env == "development" and code.startswith("mock_dev_code_"):
        # 开发模式：用 code 的 hash 模拟一个稳定的 openid
        openid = f"dev_openid_{code[-12:]}"
    else:
        # 生产模式：调微信接口
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://api.weixin.qq.com/sns/oauth2/access_token",
                params={
                    "appid": settings.wechat_app_id,
                    "secret": settings.wechat_app_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                },
            )
            data = resp.json()
            if "errcode" in data and data["errcode"] != 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"微信授权失败: {data.get('errmsg', '未知错误')}",
                )
            openid = data.get("openid", "")

    if not openid:
        raise HTTPException(status_code=400, detail="未能获取微信 openid")

    # 3. 查或建患者，发 JWT
    patient_resp = await _login_or_register_patient(
        db, wechat_openid=openid, institution_id=0,  # institution_id 后续可从 state 解析
    )

    # 4. 重定向回前端，URL 带上 token
    token = patient_resp.access_token
    redirect_url = redirect_uri or "/"
    separator = "&" if "?" in redirect_url else "?"
    final_url = f"{redirect_url}{separator}token={token}&patient_id={patient_resp.patient_id}&phone={patient_resp.phone}&name={patient_resp.name}"
    return RedirectResponse(url=final_url)


# ── 开发模式：模拟微信登录（跳过扫码） ──────────────────
@router.post("/wechat/mock-login", response_model=PatientTokenResponse)
async def wechat_mock_login(
    body: WechatMockLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """仅开发环境可用：用给定的 openid 直接登录，不调微信"""
    if settings.app_env != "development":
        raise HTTPException(status_code=403, detail="仅开发环境可用")
    return await _login_or_register_patient(
        db, wechat_openid=body.openid, institution_id=body.institution_id,
    )


# ── 发送验证码 ────────────────────────────────────────
@router.post("/send-code")
async def send_code(body: SendCodeRequest):
    code = generate_code()
    key = f"sms:{body.phone}:{body.institution_id}"
    await redis_client.set(key, code, ex=300)
    # 演示阶段：控制台打印验证码，生产环境替换为真实短信
    print(f"[SMS] 手机号: {body.phone} 验证码: {code}")
    return {"msg": "验证码已发送"}

# ── 验证码登录 ────────────────────────────────────────
@router.post("/login", response_model=PatientTokenResponse)
async def patient_login(body: PatientLoginRequest, db: AsyncSession = Depends(get_db)):
    # 1. 校验验证码
    key = f"sms:{body.phone}:{body.institution_id}"
    cached_code = await redis_client.get(key)
    if not cached_code or cached_code != body.code:
        raise HTTPException(status_code=400, detail="验证码错误或已过期")

    # 2. 验证通过，删除验证码（一次性）
    await redis_client.delete(key)

    # 3. 查或建患者记录（Get or Create）
    result = await db.execute(
        select(Patient).where(
            Patient.phone == body.phone,
            Patient.institution_id == body.institution_id,
        )
    )
    patient = result.scalar_one_or_none()

    if not patient:
        # 第一次登录，自动注册
        patient = Patient(
            phone=body.phone,
            institution_id=body.institution_id,
            name="",  # 名字后续在预约时填写
        )
        db.add(patient)
        await db.flush()  # 让 patient.id 可用

    # 4. 生成患者 JWT
    token = create_access_token({
        "sub": str(patient.id),
        "phone": patient.phone,
        "institution_id": patient.institution_id,
        "role": "patient",   # 和管理员区分开
    })

    return PatientTokenResponse(
        access_token=token,
        patient_id=patient.id,
        phone=patient.phone,
        name=patient.name,
    )