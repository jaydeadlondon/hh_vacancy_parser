from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator


class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str

    @field_validator("username")
    @classmethod
    def username_valid(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("Имя пользователя минимум 3 символа")
        if len(v) > 64:
            raise ValueError("Имя пользователя максимум 64 символа")
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Только буквы, цифры, _ и -")
        return v

    @field_validator("password")
    @classmethod
    def password_valid(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Пароль минимум 8 символов")
        return v


class UserLogin(BaseModel):
    username: str
    password: str


class UserUpdateTelegram(BaseModel):
    telegram_chat_id: str
    telegram_username: str | None = None


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    telegram_chat_id: int | None
    telegram_username: str | None
    is_active: bool
    is_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserShort(BaseModel):
    id: int
    username: str
    email: str

    model_config = {"from_attributes": True}
