import json
import os
from datetime import timedelta

from authx import AuthX, AuthXConfig
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from fastapi import HTTPException, status
from pwdlib import PasswordHash

from .redis import redis_client

load_dotenv()

ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
BACKUP_KEY = os.getenv("BACKUP_ENCRYPTION")
config = AuthXConfig(
    JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY"),
    JWT_ALGORITHM="HS256",
    JWT_TOKEN_LOCATION=["cookies"],
    JWT_ACCESS_TOKEN_EXPIRES=timedelta(minutes=30),
    JWT_ACCESS_COOKIE_NAME="auth_access_token",
)

auth = AuthX(config=config)

password_hash = PasswordHash.recommended()

cipher = Fernet(ENCRYPTION_KEY.encode())

backup_cipher = Fernet(BACKUP_KEY.encode())


def encrypt_data(data: dict) -> bytes:
    json_bytes = json.dumps(data).encode("utf-8")
    return cipher.encrypt(json_bytes)


def decrypt_data(token: bytes) -> dict:
    decrypted_bytes = cipher.decrypt(token)
    return json.loads(decrypted_bytes.decode("utf-8"))


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def hash_backups(plain: str):
    return password_hash.hash(plain)


def verify_backups(payload: str, hashed: str) -> bool:
    return password_hash.verify(payload, hashed)


async def check_attempt(user_id):
    key = f"failed_2fa: {user_id}"
    attempts = await redis_client.get(key)

    if attempts and int(attempts) >= 5:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Too many failed attempts. Try again in 20 minutes",
        )


async def register_failure(user_id):
    key = f"failed_2fa: {user_id}"
    attempts = await redis_client.incr(key)

    if attempts == 5:
        await redis_client.expire(key, 900)


async def reset_attempts(user_id):
    key = f"failed_2fa: {user_id}"
    await redis_client.delete(key)
