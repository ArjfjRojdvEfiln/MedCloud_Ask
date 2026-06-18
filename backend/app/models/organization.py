from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin

class Organization(Base, TimestampMixin):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="机构名称")
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="唯一标识符，用于URL")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")

    # 关联用户（一对多）
    users: Mapped[list["User"]] = relationship("User", back_populates="organization")
    departments: Mapped[list["Department"]] = relationship("Department", back_populates="organization")