from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.core.database import get_db
from app.models.organization import Organization
from app.models.conversation import Conversation, Message
from app.services.dify_service import dify_service
import re
from typing import Optional

router = APIRouter()


class ChatRequest(BaseModel):
    session_id: str       # 前端生成的 UUID，标识这个患者
    org_slug: str         # 机构标识，用于租户隔离
    question: str         # 患者的问题
    conversation_id: Optional[str] = None  # 多轮对话时传上一次的 dify_conversation_id


@router.post("/messages")
async def chat(
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    # 1. 用 org_slug 找机构，做租户隔离
    result = await db.execute(
        select(Organization).where(
            Organization.slug == body.org_slug,
            Organization.is_active.is_(True),
        )
    )
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="机构不存在")

    # 2. 查或建 Conversation 记录
    result = await db.execute(
        select(Conversation).where(
            Conversation.session_id == body.session_id,
            Conversation.organization_id == org.id,
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        conv = Conversation(
            organization_id=org.id,
            session_id=body.session_id,
            dify_conversation_id=body.conversation_id,
        )
        db.add(conv)
        await db.flush()

    # 3. 先把用户消息存 MySQL
    user_msg = Message(
        conversation_id=conv.id,
        role="user",
        content=body.question,
    )
    db.add(user_msg)
    await db.commit()

    # 4. 流式生成器：透传 Dify 响应，同时拼接完整回答
    full_answer = []
    dify_conv_id_holder = []  # 用列表作为可变容器，在闭包内赋值

    async def generate():
        import json
        async for chunk in dify_service.chat_stream(
            question=body.question,
            conversation_id=body.conversation_id,
        ):
            if chunk.startswith("data: "):
                try:
                    data = json.loads(chunk[6:].strip())
                    if data.get("event") == "message":
                        full_answer.append(data.get("answer", ""))
                    elif data.get("event") == "message_end":
                        cid = data.get("conversation_id")
                        if cid:
                            dify_conv_id_holder.append(cid)
                except Exception:
                    pass
            yield chunk

        # 5. 流结束后，把 AI 回答存 MySQL，并更新 dify_conversation_id
        if full_answer:
            ai_content = "".join(full_answer)
            ai_content = re.sub(r'<think>.*?</think>', '', ai_content, flags=re.DOTALL).strip()
            async with db.begin():
                ai_msg = Message(
                    conversation_id=conv.id,
                    role="assistant",
                    content=ai_content,
                )
                db.add(ai_msg)
                # 把 Dify 返回的 conversation_id 持久化，保证重启后多轮对话可续
                if dify_conv_id_holder and not conv.dify_conversation_id:
                    conv.dify_conversation_id = dify_conv_id_holder[0]
                    db.add(conv)

            # 发到 RabbitMQ，异步写 ES
            from app.core.rabbitmq import publish_message
            import datetime
            await publish_message({
                "conversation_id": conv.id,
                "organization_id": conv.organization_id,
                "session_id": body.session_id,
                "role": "assistant",
                "content": ai_content,
                "created_at": datetime.datetime.utcnow().isoformat(),
            })
            print(f"[MQ] 消息已发送到队列")

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"X-Accel-Buffering": "no"},  # 禁用 nginx 缓冲，确保实时推送
    )