import base64
import json
import time
import urllib.parse
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.config import settings
from app.core.database import get_db
from app.models.appointment import Appointment

router = APIRouter()

ALIPAY_GATEWAY = "https://openapi-sandbox.dl.alipaydev.com/gateway.do"
SERVER_BASE = "http://116.62.207.236"
NOTIFY_URL = f"{SERVER_BASE}:8001/api/v1/pay/notify"
RETURN_URL = f"{SERVER_BASE}/patient/appointment?pay=success"


def _sign(params: dict) -> str:
    """
    RSA2 签名：
    1. 参数按 key 字母序排列，拼成 key=value&key=value 字符串
    2. 用应用私钥对字符串做 SHA256withRSA 签名
    3. Base64 编码后 URL encode
    """
    # 1. 排序拼接
    sorted_params = sorted(params.items())
    sign_str = "&".join(f"{k}={v}" for k, v in sorted_params)

    # 2. 加载私钥（PKCS8 格式，需要包裹 header）
    private_key_str = (
            "-----BEGIN RSA PRIVATE KEY-----\n"
            + settings.alipay_app_private_key
            + "\n-----END RSA PRIVATE KEY-----"
    )
    key = RSA.importKey(private_key_str)

    # 3. SHA256withRSA 签名
    h = SHA256.new(sign_str.encode("utf-8"))
    signature = pkcs1_15.new(key).sign(h)

    # 4. Base64 编码
    return base64.b64encode(signature).decode("utf-8")


def _verify(params: dict, signature: str) -> bool:
    """
    验证支付宝回调签名
    """
    try:
        public_key_str = (
            "-----BEGIN PUBLIC KEY-----\n"
            + settings.alipay_public_key
            + "\n-----END PUBLIC KEY-----"
        )
        key = RSA.importKey(public_key_str)

        sorted_params = sorted(params.items())
        sign_str = "&".join(f"{k}={v}" for k, v in sorted_params)

        h = SHA256.new(sign_str.encode("utf-8"))
        sig_bytes = base64.b64decode(signature)
        pkcs1_15.new(key).verify(h, sig_bytes)
        return True
    except Exception:
        return False


def build_pay_url(appointment_id: int, amount: float) -> str:
    """
    拼接支付宝电脑网页支付跳转 URL
    """
    biz_content = json.dumps({
        "out_trade_no": f"appt-{appointment_id}",
        "product_code": "FAST_INSTANT_TRADE_PAY",
        "total_amount": f"{amount:.2f}",
        "subject": f"医云问预约挂号#{appointment_id}",
    }, ensure_ascii=False, separators=(",", ":"))

    params = {
        "app_id": settings.alipay_app_id,
        "method": "alipay.trade.page.pay",
        "charset": "utf-8",
        "sign_type": "RSA2",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "version": "1.0",
        "notify_url": NOTIFY_URL,
        "return_url": RETURN_URL,
        "biz_content": biz_content,
    }

    # 生成签名
    params["sign"] = _sign(params)

    # 拼接完整 URL
    query_string = urllib.parse.urlencode(params)
    return f"{ALIPAY_GATEWAY}?{query_string}"


# ── 路由 ──────────────────────────────────────────

class PayCreateRequest(BaseModel):
    appointment_id: int
    amount: float = 99.00


@router.post("/create")
async def create_pay_order(
    body: PayCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """创建支付宝订单，返回跳转 URL"""
    appt = await db.get(Appointment, body.appointment_id)
    if not appt:
        raise HTTPException(status_code=404, detail="预约不存在")

    pay_url = build_pay_url(body.appointment_id, body.amount)
    return {"pay_url": pay_url, "order_no": f"appt-{body.appointment_id}"}


@router.post("/notify")
async def alipay_notify(request: Request, db: AsyncSession = Depends(get_db)):
    """支付宝异步回调，验签后更新预约状态"""
    form_data = await request.form()
    data = dict(form_data)

    # 取出签名，剩余字段用于验签
    signature = data.pop("sign", "")
    data.pop("sign_type", None)  # sign_type 不参与验签

    if not _verify(data, signature):
        return JSONResponse(content="fail", status_code=400)

    trade_status = data.get("trade_status", "")
    out_trade_no = data.get("out_trade_no", "")

    if trade_status in ("TRADE_SUCCESS", "TRADE_FINISHED"):
        try:
            appointment_id = int(out_trade_no.replace("appt-", ""))
        except ValueError:
            return JSONResponse(content="fail", status_code=400)

        appt = await db.get(Appointment, appointment_id)
        if appt and appt.status == "pending":
            appt.status = "confirmed"
            await db.commit()

    # 必须返回 "success"，否则支付宝会反复重试
    return JSONResponse(content="success")