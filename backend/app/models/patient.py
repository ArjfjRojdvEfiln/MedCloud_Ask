from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint, Index
from sqlalchemy.sql import func
from app.models.base import Base

class Patient(Base):
    __tablename__ = "patients"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    phone          = Column(String(20), nullable=False)
    name           = Column(String(50), nullable=False, default="")
    wechat_openid  = Column(String(128), nullable=True)          # 微信 openid，微信登录绑定
    institution_id = Column(Integer, nullable=False)
    created_at     = Column(DateTime, server_default=func.now())

    # 联合唯一约束：同一机构内手机号唯一
    __table_args__ = (
        UniqueConstraint("phone", "institution_id", name="uq_patient_phone_institution"),
        Index("ix_patient_wechat_openid", "wechat_openid"),     # 按 openid 查患者加速
    )