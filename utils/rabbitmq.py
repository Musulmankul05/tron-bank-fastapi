import json
import os

import aio_pika
from aio_pika.abc import AbstractRobustChannel, AbstractRobustConnection


class RabbitMQService:
    def __init__(self):
        self.connection: AbstractRobustConnection | None = None
        self.channel: AbstractRobustChannel | None = None

    async def connect(self):
        url = os.getenv("RABBITMQ_URL")
        self.connection = await aio_pika.connect_robust(url)
        self.channel = await self.connection.channel()

    async def close(self):
        if self.connection:
            await self.connection.close()

    async def publish_event(
        self, routing_key: str, message_body: dict, exchange_name: str = "bank_events"
    ):
        if not self.channel:
            raise RuntimeError("RabbitMQ channel is not initialized!")

        exchange = await self.channel.declare_exchange(
            name=exchange_name,
            type=aio_pika.ExchangeType.TOPIC,
            durable=True,
        )

        message = aio_pika.Message(
            body=json.dumps(message_body).encode("utf-8"),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )

        await exchange.publish(message, routing_key=routing_key)


rabbitmq_service = RabbitMQService()
