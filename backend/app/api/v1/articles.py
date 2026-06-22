from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.article import Article

router = APIRouter()


class ArticleCreate(BaseModel):
    title: str
    content: str
    tags: Optional[str] = ""
    organization_id: int  # 前端会传，但我们以 JWT 里的为准


class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[str] = None
    is_published: Optional[bool] = None


@router.get("/")
async def list_articles(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    文章列表——只返回当前机构的文章
    """
    result = await db.execute(
        select(Article)
        .where(Article.organization_id == current_user.organization_id)
        .order_by(Article.created_at.desc())
    )
    articles = result.scalars().all()

    return [
        {
            "id": a.id,
            "title": a.title,
            "content": a.content,
            "tags": a.tags or "",
            "is_published": a.is_published,
            "created_at": a.created_at.isoformat(),
        }
        for a in articles
    ]


@router.post("/", status_code=201)
async def create_article(
    body: ArticleCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    新建文章——organization_id 强制用 JWT 里的，忽略前端传的值
    """
    article = Article(
        organization_id=current_user.organization_id,  # 不信任前端传的 org_id
        title=body.title,
        content=body.content,
        tags=body.tags,
        is_published=False,  # 新建默认草稿
    )
    db.add(article)
    await db.commit()
    await db.refresh(article)

    return {
        "id": article.id,
        "title": article.title,
        "content": article.content,
        "tags": article.tags or "",
        "is_published": article.is_published,
        "created_at": article.created_at.isoformat(),
    }


@router.patch("/{article_id}")
async def update_article(
    article_id: int,
    body: ArticleUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    编辑文章内容 或 切换上线/下线状态
    两种操作共用同一个接口，前端传哪个字段就更新哪个
    """
    article = await db.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    if article.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="无权操作")

    # 只更新前端传了的字段（None 表示没传，跳过）
    if body.title is not None:
        article.title = body.title
    if body.content is not None:
        article.content = body.content
    if body.tags is not None:
        article.tags = body.tags
    if body.is_published is not None:
        article.is_published = body.is_published

    await db.commit()
    return {"msg": "更新成功"}


@router.delete("/{article_id}", status_code=204)
async def delete_article(
    article_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    删除文章——同样校验归属
    """
    article = await db.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    if article.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="无权操作")

    await db.delete(article)
    await db.commit()