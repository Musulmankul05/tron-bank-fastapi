import json
from datetime import timedelta

from authx import AuthX, AuthXConfig
from cryptography.fernet import Fernet
from pwdlib import PasswordHash

ENCRYPTION_KEY = 'n5dgxSL5IYwoHd0ncddSoqv-IuqmI4qIbC99KNAdLZ4='

config = AuthXConfig(
    JWT_SECRET_KEY="vu389F8p9q33fnk&ja389cKergoi4389",
    JWT_ALGORITHM="HS256",
    JWT_TOKEN_LOCATION=["cookies"],
    JWT_ACCESS_TOKEN_EXPIRES=timedelta(minutes=30),
    JWT_ACCESS_COOKIE_NAME="auth_access_token",
)

auth = AuthX(config=config)

password_hash = PasswordHash.recommended()

cipher = Fernet(ENCRYPTION_KEY.encode())

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
