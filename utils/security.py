from datetime import timedelta

from authx import AuthX, AuthXConfig
from pwdlib import PasswordHash

config = AuthXConfig(
    JWT_SECRET_KEY="vu389F8p9q33fnk&ja389cKergoi4389",
    JWT_ALGORITHM="HS256",
    JWT_TOKEN_LOCATION=['cookies'],
    JWT_ACCESS_TOKEN_EXPIRES=timedelta(minutes=30),
    JWT_ACCESS_COOKIE_NAME="auth_access_token"
)

auth = AuthX(config=config)

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)

