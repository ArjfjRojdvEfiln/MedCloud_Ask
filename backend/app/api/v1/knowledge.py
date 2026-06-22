from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.knowledge import KnowledgeBase, KnowledgeDocument
from app.services.dify_service import dify_service

router = APIRouter()

# 允许上传的文件类型
ALLOWED_TYPES = {
    "application/pdf": "pdf",
    "text/plain": "txt",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
}


async def get_or_create_knowledge_base(
    db: AsyncSession, organization_id: int
) -> KnowledgeBase:
    """
    Get or Create 模式：
    有就返回现有的，没有就自动创建一条
    """
    result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.organization_id == organization_id
        )
    )
    kb = result.scalar_one_or_none()

    if kb is None:
        # 第一次上传，自动建一条知识库记录
        kb = KnowledgeBase(
            organization_id=organization_id,
            name="默认知识库",
            dify_dataset_id=dify_service.dataset_id,
        )
        db.add(kb)
        await db.flush()  # 让 kb.id 可用，但不提交

    return kb


@router.post("/upload", status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    print(f"[DEBUG] filename={file.filename}, content_type={file.content_type}")
    # 1. 检查文件类型
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型：{file.content_type}，仅支持 PDF / TXT / DOCX",
        )

    # 2. 读取文件内容（上传到内存，文件不大，够用）
    file_content = await file.read()

    # 3. Get or Create 知识库记录
    kb = await get_or_create_knowledge_base(db, current_user.organization_id)

    # 4. 转发给 Dify
    try:
        dify_result = await dify_service.upload_document(
            filename=file.filename,
            file_content=file_content,
            content_type=file.content_type,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Dify 服务异常：{str(e)}")

    # 5. 把文档记录写入 knowledge_documents 表
    doc = KnowledgeDocument(
        knowledge_base_id=kb.id,
        filename=file.filename,
        oss_url="",   # 文档存在 Dify，这里留空或存 dify 的 document_id
        status="processing",  # Dify 还在向量化，先标 processing
    )
    db.add(doc)
    # get_db() 会自动 commit，不需要手动写

    return {
        "msg": "上传成功，Dify 正在处理",
        "filename": file.filename,
        "dify_document_id": dify_result.get("document", {}).get("id"),
        "status": "processing",
    }