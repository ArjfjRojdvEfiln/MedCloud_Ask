from alibabacloud_dysmsapi20170525.client import Client
from alibabacloud_dysmsapi20170525 import models as sms_models
from alibabacloud_tea_openapi import models as open_api_models
from app.core.config import settings
import random


def _create_client() -> Client:
    """创建阿里云短信客户端"""
    config = open_api_models.Config(
        access_key_id=settings.oss_access_key_id,       # 复用 OSS 的 AccessKey
        access_key_secret=settings.oss_access_key_secret,
    )
    config.endpoint = "dysmsapi.aliyuncs.com"
    return Client(config)


def generate_code() -> str:
    """生成6位随机数字验证码"""
    return str(random.randint(100000, 999999))


def send_sms(phone: str, code: str) -> bool:
    """
    发送验证码短信
    :param phone: 目标手机号
    :param code: 验证码
    :return: 是否发送成功
    """
    try:
        client = _create_client()
        request = sms_models.SendSmsRequest(
            phone_numbers=phone,
            sign_name=settings.sms_sign_name,
            template_code=settings.sms_template_code,
            template_param=f'{{"code":"{code}"}}',  # 模板变量，对应 ${code}
        )
        response = client.send_sms(request)
        # Code == "OK" 表示发送成功
        if response.body.code == "OK":
            return True
        else:
            print(f"[SMS] 发送失败：{response.body.code} - {response.body.message}")
            return False
    except Exception as e:
        print(f"[SMS] 异常：{e}")
        return False