from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.schemas.user import UserResponse, UserUpdateTelegram
from shared.models.user import User

router = APIRouter(prefix="/users", tags=["users"])


@router.patch("/me/telegram", response_model=UserResponse)
async def update_telegram(
    data: UserUpdateTelegram,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Привязываем Telegram аккаунт"""
    current_user.telegram_chat_id = data.telegram_chat_id
    current_user.telegram_username = data.telegram_username
    await db.flush()
    await db.refresh(current_user)
    return current_user
