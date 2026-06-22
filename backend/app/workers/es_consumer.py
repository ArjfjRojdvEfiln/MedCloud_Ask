import json
import asyncio
import aio_pika
from elasticsearch import AsyncElasticsearch
from app.core.config import settings
from app.core.rabbitmq import QUEUE_NAME

# ES 客户端
es = AsyncElasticsearch(settings.es_url)
ES_INDEX = "messages"  # ES 索引名


async def ensure_index():
    """确保 ES 索引存在，不存在就创建"""
    exists = await es.indices.exists(index=ES_INDEX)
    if not exists:
        await es.indices.create(
            index=ES_INDEX,
            body={
                "mappings": {
                    "properties": {
                        "conversation_id": {"type": "integer"},
                        "organization_id": {"type": "integer"},
                        "role": {"type": "keyword"},
                        "content": {"type": "text"},
                        "session_id": {"type": "keyword"},
                        "created_at": {"type": "date"},
                    }
                }
            },
        )
        print(f"[ES] 索引 {ES_INDEX} 创建成功")


async def handle_message(message: aio_pika.IncomingMessage):
    """处理从队列取出的每条消息"""
    async with message.process():  # 自动 ack/nack
        try:
            data = json.loads(message.body.decode())
            print(f"[Consumer] 收到消息：{data}")

            # 写入 ES
            await es.index(
                index=ES_INDEX,
                document={
                    "conversation_id": data["conversation_id"],
                    "organization_id": data["organization_id"],
                    "session_id": data["session_id"],
                    "role": data["role"],
                    "content": data["content"],
                    "created_at": data["created_at"],
                },
            )
            print(f"[ES] 写入成功：{data['role']} - {data['content'][:20]}")
        except Exception as e:
            print(f"[Consumer] 处理失败：{e}")
            # message.process() 会自动 nack，消息重回队列


async def main():
    print("[Consumer] 启动，等待消息...")
    await ensure_index()

    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=10)  # 每次最多处理10条

    queue = await channel.declare_queue(QUEUE_NAME, durable=True)
    await queue.consume(handle_message)

    print(f"[Consumer] 监听队列：{QUEUE_NAME}")
    await asyncio.Future()  # 永久阻塞，保持消费者运行


if __name__ == "__main__":
    asyncio.run(main())