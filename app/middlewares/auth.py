from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from app.models import UserModel


class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Foydalanuvchi ma'lumotlarini olish
        user = None
        if isinstance(event, Message) and event.from_user:
            user = event.from_user
        elif isinstance(event, CallbackQuery) and event.from_user:
            user = event.from_user

        if user:
            db_user, created = await UserModel.get_or_create(
                telegram_id=user.id,
                full_name=user.full_name,
                username=user.username
            )

            # Bloklangan foydalanuvchini tekshirish
            if db_user.get("is_blocked"):
                if isinstance(event, Message):
                    await event.answer("❌ Siz bloklangansiz. Admin bilan bog'laning.")
                elif isinstance(event, CallbackQuery):
                    await event.answer("❌ Siz bloklangansiz!", show_alert=True)
                return

            data["db_user"] = db_user
            data["is_new_user"] = created

        return await handler(event, data)
