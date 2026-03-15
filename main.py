import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings
from app.models.database import connect_db, close_db
from app.handlers import main_router
from app.middlewares import AuthMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def on_startup(bot: Bot):
    await connect_db()
    logger.info(f"✅ Bot ishga tushdi: @{(await bot.get_me()).username}")

    # Admin'larga xabar
    for admin_id in settings.admin_ids_list:
        try:
            await bot.send_message(admin_id, "✅ Bot ishga tushdi!")
        except Exception:
            pass


async def on_shutdown(bot: Bot):
    await close_db()
    logger.info("❌ Bot to'xtatildi")


async def main():
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Middleware — Message va CallbackQuery uchun alohida
    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(AuthMiddleware())

    # Routerlar
    dp.include_router(main_router)

    # Startup/Shutdown
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    logger.info("🚀 Bot ishga tushmoqda...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
