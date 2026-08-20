import os

import redis.asyncio as aioredis
from dotenv import load_dotenv

load_dotenv()


def get_redis():
    return aioredis.from_url(
        os.getenv("REDIS_URL"),
        decode_responses=True,
    )