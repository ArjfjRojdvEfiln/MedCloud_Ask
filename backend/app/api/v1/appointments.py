from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
import redis.asyncio as redis
from app.core.database import get_db
from app.core.redis_client import get_redis
from app.models.appointment import TimeSlot, Appointment

router = APIRouter()


class AppointmentRequest(BaseModel):
    time_slot_id: int
    patient_name: str
    patient_phone: str
    organization_id: int


@router.post("/", status_code=201)
async def create_appointment(
    body: AppointmentRequest,
    db: AsyncSession = Depends(get_db),
    rc: redis.Redis = Depends(get_redis),
):
    # ── 第一步：防重复，Redis SET NX ──────────────────
    dedup_key = f"appt:dedup:{body.patient_phone}:{body.time_slot_id}"
    # nx=True：只有 key 不存在时才设置，返回 True 表示占坑成功
    # ex=604800：7天过期（秒）
    is_new = await rc.set(dedup_key, "1", nx=True, ex=604800)
    if not is_new:
        raise HTTPException(status_code=400, detail="您已预约该时间段，请勿重复预约")

    # ── 第二步：分布式锁，防并发超卖 ──────────────────
    lock_key = f"appt:lock:{body.time_slot_id}"
    # nx=True + ex=10：最多持锁10秒，防止死锁
    lock = await rc.set(lock_key, "1", nx=True, ex=10)
    if not lock:
        # 拿不到锁，说明有人正在预约这个时间段
        # 同时把刚才占的去重坑位释放掉
        await rc.delete(dedup_key)
        raise HTTPException(status_code=429, detail="系统繁忙，请稍后重试")

    try:
        # ── 第三步：查余号 ────────────────────────────
        slot = await db.get(TimeSlot, body.time_slot_id)
        if not slot:
            raise HTTPException(status_code=404, detail="时间段不存在")
        if slot.remaining <= 0:
            raise HTTPException(status_code=400, detail="该时间段号源已满")

        # ── 第四步：扣减号源 + 创建预约记录 ──────────
        slot.remaining -= 1
        appointment = Appointment(
            organization_id=body.organization_id,
            department_id=slot.department_id,
            time_slot_id=slot.id,
            patient_name=body.patient_name,
            patient_phone=body.patient_phone,
            status="pending",
        )
        db.add(appointment)
        await db.commit()

        return {
            "msg": "预约成功",
            "appointment_id": appointment.id,
            "status": "pending",
        }

    except HTTPException:
        # HTTPException 需要先清掉去重 key 再重新抛出
        await rc.delete(dedup_key)
        raise

    finally:
        # ── 无论成功失败，都释放分布式锁 ──────────────
        await rc.delete(lock_key)