import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from app.core.config import settings
from app.handlers import filters, start, vacancies
from app.middlewares.auth import AuthMiddleware
from shared.utils.logger import get_logger

logger = get_logger(__name__)


async def main() -> None:
    storage = RedisStorage.from_url(settings.redis_url)

    bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher(storage=storage)

    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(AuthMiddleware())

    dp.include_router(start.router)
    dp.include_router(filters.router)
    dp.include_router(vacancies.router)

    logger.info("🤖 Telegram Bot запущен")

    try:
        await dp.start_polling(
            bot,
            allowed_updates=["message", "callback_query"],
        )
    finally:
        await bot.session.close()
        logger.info("👋 Bot остановлен")


if __name__ == "__main__":
    asyncio.run(main())
