from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt
from passlib.context import CryptContext

from .config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"
TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"


def hash_password(password: str) -> str:
    """Хэшируем пароль — обрезаем до 72 байт для bcrypt"""
    return pwd_context.hash(password[:72])


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяем пароль против хэша"""
    return pwd_context.verify(plain_password[:72], hashed_password)


def create_access_token(subject: int | str, extra: dict[str, Any] | None = None) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": str(subject),
        "type": TOKEN_TYPE_ACCESS,
        "iat": now,
        "exp": expire,
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.api_secret_key, algorithm=ALGORITHM)


def create_refresh_token(subject: int | str) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.refresh_token_expire_days)
    payload = {
        "sub": str(subject),
        "type": TOKEN_TYPE_REFRESH,
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(payload, settings.api_secret_key, algorithm=ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.api_secret_key, algorithms=[ALGORITHM])


def verify_token_type(payload: dict[str, Any], expected_type: str) -> bool:
    return payload.get("type") == expected_type
