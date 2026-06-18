from sqlalchemy import String, Integer, ForeignKey, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin

class KnowledgeBase(Base, TimestampMixin):
    __tablename__ = "knowledge_bases"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=False, unique=True,
        comment="一个机构只有一个知识库"
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    dify_dataset_id: Mapped[str] = mapped_column(
        String(100), nullable=True, comment="Dify 平台上对应的知识库ID"
    )

    documents: Mapped[list["KnowledgeDocument"]] = relationship(
        "KnowledgeDocument", back_populates="knowledge_base"
    )

class KnowledgeDocument(Base, TimestampMixin):
    __tablename__ = "knowledge_documents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    knowledge_base_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("knowledge_bases.id"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False, comment="原始文件名")
    oss_url: Mapped[str] = mapped_column(String(500), nullable=False, comment="文件在OSS的访问地址")
    status: Mapped[str] = mapped_column(
        String(20), default="processing",
        comment="processing/ready/failed"
    )

    knowledge_base: Mapped["KnowledgeBase"] = relationship(
        "KnowledgeBase", back_populates="documents"
    )
