from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from pydantic import BaseModel
from typing import Optional
import redis.asyncio as redis
from app.core.database import get_db
from app.core.redis_client import get_redis
from app.core.deps import get_current_user
from app.models.user import User
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


@router.get("/")
async def list_appointments(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    预约列表——organization_id 从 JWT 取，防水平越权
    支持 ?status=pending/confirmed/cancelled 过滤
    """
    stmt = (
        select(Appointment)
        .options(
            joinedload(Appointment.department),
            joinedload(Appointment.time_slot),
        )
        .where(Appointment.organization_id == current_user.organization_id)
        .order_by(Appointment.created_at.desc())
    )

    if status:
        stmt = stmt.where(Appointment.status == status)

    result = await db.execute(stmt)
    appointments = result.scalars().all()

    return [
        {
            "id": a.id,
            "patient_name": a.patient_name,
            "patient_phone": a.patient_phone,
            "department_name": a.department.name,
            "slot_date": str(a.time_slot.date),
            "slot_time": f"{a.time_slot.start_time}-{a.time_slot.end_time}",
            "status": a.status,
            "created_at": a.created_at.isoformat(),
        }
        for a in appointments
    ]


class AppointmentStatusUpdate(BaseModel):
    status: str  # confirmed 或 cancelled


@router.patch("/{appointment_id}")
async def update_appointment_status(
    appointment_id: int,
    body: AppointmentStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    确认或取消预约
    - 同样用 organization_id 做权限校验，不能操作别家机构的预约
    - 取消时自动释放号源（remaining + 1）
    """
    # 1. 查预约，同时校验归属
    appt = await db.get(Appointment, appointment_id)
    if not appt:
        raise HTTPException(status_code=404, detail="预约不存在")
    if appt.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="无权操作")

    # 2. 校验状态流转是否合法（只有 pending 才能被操作）
    if appt.status != "pending":
        raise HTTPException(status_code=400, detail=f"当前状态 {appt.status} 不可修改")

    # 3. 取消时释放号源
    if body.status == "cancelled":
        slot = await db.get(TimeSlot, appt.time_slot_id)
        if slot:
            slot.remaining += 1  # 号源归还

    appt.status = body.status
    await db.commit()

    return {"msg": "操作成功", "status": appt.status}