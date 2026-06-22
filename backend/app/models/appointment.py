from sqlalchemy import String, Integer, ForeignKey, Date, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin
import datetime

class Department(Base, TimestampMixin):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="科室名称")

    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="departments"
    )
    time_slots: Mapped[list["TimeSlot"]] = relationship(
        "TimeSlot", back_populates="department"
    )
    appointments: Mapped[list["Appointment"]] = relationship(
        "Appointment", back_populates="department"
    )

class TimeSlot(Base, TimestampMixin):
    __tablename__ = "time_slots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    department_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("departments.id"), nullable=False
    )
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    start_time: Mapped[datetime.time] = mapped_column(Time, nullable=False)
    end_time: Mapped[datetime.time] = mapped_column(Time, nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, default=1, comment="该时段总号源数")
    remaining: Mapped[int] = mapped_column(Integer, default=1, comment="剩余号源数")

    department: Mapped["Department"] = relationship(
        "Department", back_populates="time_slots"
    )

class Appointment(Base, TimestampMixin):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False
    )
    department_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("departments.id"), nullable=False
    )
    time_slot_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("time_slots.id"), nullable=False
    )
    patient_name: Mapped[str] = mapped_column(String(50), nullable=False)
    patient_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="pending",
        comment="pending/confirmed/cancelled"
    )

    department: Mapped["Department"] = relationship(
        "Department", back_populates="appointments"
    )
    time_slot: Mapped["TimeSlot"] = relationship("TimeSlot")
