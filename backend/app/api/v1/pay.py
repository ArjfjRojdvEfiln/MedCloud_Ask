from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from alipay import AliPay
from app.core.config import settings
from app.core.database import get_db
from app.models.appointment import Appointment

router = APIRouter()

ALIPAY_GATEWAY_SANDBOX = "https://openapi-sandbox.dl.alipaydev.com/gateway.do"
SERVER_BASE = "http://116.62.207.236"


def get_alipay_client() -> AliPay:
    """
    初始化支付宝沙箱客户端
    私钥/公钥需要包裹 PEM header，SDK 才能正确解析
    """
    app_private_key = (
        "-----BEGIN PRIVATE KEY-----\n"
        + settings.alipay_app_private_key
        + "\n-----END PRIVATE KEY-----"
    )
    alipay_public_key = (
        "-----BEGIN PUBLIC KEY-----\n"
        + settings.alipay_public_key
        + "\n-----END PUBLIC KEY-----"
    )
    return AliPay(
        appid=settings.alipay_app_id,
        app_notify_url=f"{SERVER_BASE}:8001/api/v1/pay/notify",
        app_private_key_string=app_private_key,
        alipay_public_key_string=alipay_public_key,
        sign_type="RSA2",
        debug=True,  # True = 沙箱网关
    )


class PayCreateRequest(BaseModel):
    appointment_id: int
    amount: float = 99.00  # 演示挂号费


@router.post("/create")
async def create_pay_order(
    body: PayCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    创建支付宝网页支付订单，返回跳转 URL
    前端拿到 pay_url 后直接 window.location.href 跳转
    """
    # 1. 确认预约存在
    appt = await db.get(Appointment, body.appointment_id)
    if not appt:
        raise HTTPException(status_code=404, detail="预约不存在")

    alipay = get_alipay_client()

    # 2. 生成签名后的订单参数字符串
    order_string = alipay.api_alipay_trade_page_pay(
        subject=f"医云问预约挂号#{body.appointment_id}",
        out_trade_no=f"appt-{body.appointment_id}",  # 商户订单号，用预约ID保证唯一
        total_amount=f"{body.amount:.2f}",
        return_url=f"{SERVER_BASE}/patient/appointment?org=beijing-smile&pay=success",
        notify_url=f"{SERVER_BASE}:8001/api/v1/pay/notify",
    )

    # 3. 拼接沙箱网关完整 URL
    pay_url = f"{ALIPAY_GATEWAY_SANDBOX}?{order_string}"

    return {"pay_url": pay_url, "order_no": f"appt-{body.appointment_id}"}


@router.post("/notify")
async def alipay_notify(request: Request, db: AsyncSession = Depends(get_db)):
    """
    支付宝异步回调（支付宝服务器主动 POST 过来）
    - 必须验签，防止伪造回调
    - 成功后把预约状态改为 confirmed
    - 必须返回纯文本 "success"，否则支付宝会反复重试
    """
    # 1. 读取表单数据
    form_data = await request.form()
    data = dict(form_data)

    # 2. 单独取出签名（验签时不能带 sign 字段）
    signature = data.pop("sign", None)

    alipay = get_alipay_client()

    # 3. 验签
    is_valid = alipay.verify(data, signature)
    if not is_valid:
        return JSONResponse(content="fail", status_code=400)

    # 4. 只处理支付成功的状态
    trade_status = data.get("trade_status", "")
    out_trade_no = data.get("out_trade_no", "")  # 格式：appt-{id}

    if trade_status in ("TRADE_SUCCESS", "TRADE_FINISHED"):
        try:
            appointment_id = int(out_trade_no.replace("appt-", ""))
        except ValueError:
            return JSONResponse(content="fail", status_code=400)

        appt = await db.get(Appointment, appointment_id)
        # 只有 pending 状态才能流转，防止重复回调重复处理
        if appt and appt.status == "pending":
            appt.status = "confirmed"
            await db.commit()

    # 5. 必须返回 "success" 字符串
    return JSONResponse(content="success")