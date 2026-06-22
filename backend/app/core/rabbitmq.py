import json
import aio_pika
from app.core.config import settings

# 队列名称，生产者和消费者要一致
QUEUE_NAME = "conversation_messages"


async def get_rabbitmq_channel():
    """建立 RabbitMQ 连接，返回 channel"""
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    channel = await connection.channel()
    # 声明队列，durable=True 保证 RabbitMQ 重启后队列不丢失
    await channel.declare_queue(QUEUE_NAME, durable=True)
    return connection, channel


async def publish_message(message: dict):
    """
    生产者：往队列里扔一条消息
    message 是一个字典，会被序列化成 JSON
    """
    connection, channel = await get_rabbitmq_channel()
    try:
        await channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(message, ensure_ascii=False).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,  # 消息持久化，不怕重启丢
            ),
            routing_key=QUEUE_NAME,
        )
    finally:
        await connection.close()