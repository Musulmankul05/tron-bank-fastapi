import asyncio
import os

import aio_pika
from dotenv import load_dotenv

load_dotenv()


async def main():
    url = os.getenv("RABBITMQ_URL")
    connection = await aio_pika.connect_robust(url)
    channel = await connection.channel()
    
    exchange = await channel.declare_exchange(
        name="bank_events",
        type=aio_pika.ExchangeType.TOPIC,
        durable=True,
    )

    dlx_exchange = await channel.declare_exchange(
        name="bank_events.dlx",
        type=aio_pika.ExchangeType.TOPIC,
        durable=True,
    )
        
    dlq_queue = await channel.declare_queue(
        name="transaction_notifications_dlq",
        durable=True,
    )

    await dlq_queue.bind(dlx_exchange, routing_key="transfer.created")
            
    queue = await channel.declare_queue(
        name="transaction_notifications",
        durable=True,
        arguments={
            "x-dead-letter-exchange": "bank_events.dlx",  # Куда отсылать бракованные задачи
            "x-dead-letter-routing-key": "transfer.created",
        },
    )
    await queue.bind(exchange, routing_key="transfer.created")

    print("[Worker] Waiting for events...")

    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            try:
                data = message.body.decode()
                print(f"[Worker] Process: {data}")

                import json
                payload = json.loads(data)
                if payload.get("amount", 0) < 0:
                    raise ValueError("Amount cannot be under 0!")
                await message.ack()
            except Exception as e:
                print(f"[Worker ERROR] {e}. Sent to DLQ...")
                await message.reject(requeue=False)


if __name__ == "__main__":
    asyncio.run(main())
