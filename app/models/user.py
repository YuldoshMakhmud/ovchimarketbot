from datetime import datetime
from typing import Optional
from .database import get_db


class UserModel:
    # Bot foydalanuvchilari alohida collectionda — ilova users bilan aralashmasin
    collection_name = "bot_users"

    @classmethod
    def col(cls):
        return get_db().collection(cls.collection_name)

    @classmethod
    async def create(cls, telegram_id: int, full_name: str,
                     username: Optional[str] = None,
                     phone: Optional[str] = None) -> dict:
        user = {
            "telegram_id": telegram_id,
            "full_name": full_name,
            "username": username,
            "phone": phone,
            "is_blocked": False,
            "is_admin": False,
            "language": "uz",
            "source": "telegram_bot",          # qayerdan kelgani
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        await cls.col().document(str(telegram_id)).set(user)
        user["id"] = str(telegram_id)
        return user

    @classmethod
    async def get_by_telegram_id(cls, telegram_id: int) -> Optional[dict]:
        doc = await cls.col().document(str(telegram_id)).get()
        if doc.exists:
            data = doc.to_dict()
            data["id"] = doc.id
            return data
        return None

    @classmethod
    async def get_or_create(cls, telegram_id: int, full_name: str,
                             username: Optional[str] = None) -> tuple[dict, bool]:
        user = await cls.get_by_telegram_id(telegram_id)
        if user:
            # Mavjud foydalanuvchi — ismini yangilash
            await cls.col().document(str(telegram_id)).update({
                "full_name": full_name,
                "username": username,
                "updated_at": datetime.utcnow()
            })
            user["full_name"] = full_name
            return user, False
        # Yangi foydalanuvchi — yaratish
        user = await cls.create(telegram_id, full_name, username)
        return user, True

    @classmethod
    async def update_phone(cls, telegram_id: int, phone: str):
        await cls.col().document(str(telegram_id)).update({
            "phone": phone,
            "updated_at": datetime.utcnow()
        })

    @classmethod
    async def update_field(cls, telegram_id: int, **kwargs):
        kwargs["updated_at"] = datetime.utcnow()
        await cls.col().document(str(telegram_id)).update(kwargs)

    @classmethod
    async def get_all(cls, limit: int = 10000) -> list:
        result = []
        async for doc in cls.col().limit(limit).stream():
            data = doc.to_dict()
            data["id"] = doc.id
            result.append(data)
        return result

    @classmethod
    async def count(cls) -> int:
        agg = await cls.col().count().get()
        return agg[0][0].value

    @classmethod
    async def block_user(cls, telegram_id: int, blocked: bool = True):
        await cls.col().document(str(telegram_id)).update({
            "is_blocked": blocked,
            "updated_at": datetime.utcnow()
        })

    @classmethod
    async def get_active_users(cls) -> list:
        """Bloklangan bo'lmagan barcha foydalanuvchilar (broadcast uchun)"""
        result = []
        async for doc in cls.col().stream():
            data = doc.to_dict()
            if not data.get("is_blocked", False):
                data["id"] = doc.id
                result.append(data)
        return result
