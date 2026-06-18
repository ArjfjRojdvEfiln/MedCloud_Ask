from sqlalchemy import String, Integer, ForeignKey, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin

class Article(Base, TimestampMixin):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="富文本内容")
    tags: Mapped[str] = mapped_column(
        String(200), nullable=True, comment="逗号分隔的标签，如：口腔健康,体检须知"
    )
    is_published: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="是否已上线"
    )
