from datetime import datetime
from typing import Optional
from .database import get_db


class CategoryModel:
    collection_name = "categories"

    @classmethod
    def col(cls):
        return get_db().collection(cls.collection_name)

    @classmethod
    async def create(cls, name: str, description: str = "",
                     photo: Optional[str] = None) -> dict:
        import uuid
        doc_id = str(uuid.uuid4())
        category = {
            "name": name,
            "description": description,
            "image": photo,
            "priority": 0,
            "created_at": datetime.utcnow(),
        }
        await cls.col().document(doc_id).set(category)
        category["id"] = doc_id
        category["_id"] = doc_id
        return category

    @classmethod
    async def get_all_active(cls) -> list:
        # ilovada is_active yo'q — hammasi aktiv hisoblanadi
        result = []
        async for doc in cls.col().stream():
            data = doc.to_dict()
            data["id"] = doc.id
            data["_id"] = doc.id
            # bot ichida is_active ishlatilsa True qaytarsin
            data.setdefault("is_active", True)
            result.append(data)
        # priority bo'yicha sort
        result.sort(key=lambda x: x.get("priority", 0))
        return result

    @classmethod
    async def get_by_id(cls, category_id: str) -> Optional[dict]:
        doc = await cls.col().document(category_id).get()
        if doc.exists:
            data = doc.to_dict()
            data["id"] = doc.id
            data["_id"] = doc.id
            data.setdefault("is_active", True)
            return data
        return None

    @classmethod
    async def get_all(cls) -> list:
        result = []
        async for doc in cls.col().stream():
            data = doc.to_dict()
            data["id"] = doc.id
            data["_id"] = doc.id
            data.setdefault("is_active", True)
            result.append(data)
        result.sort(key=lambda x: x.get("priority", 0))
        return result

    @classmethod
    async def get_by_name(cls, name: str) -> Optional[dict]:
        """Kategoriya nomiga qarab topish (mahsulotlar uchun)"""
        async for doc in cls.col().stream():
            data = doc.to_dict()
            if data.get("name") == name:
                data["id"] = doc.id
                data["_id"] = doc.id
                return data
        return None

    @classmethod
    async def update(cls, category_id: str, **kwargs) -> bool:
        kwargs["updated_at"] = datetime.utcnow()
        await cls.col().document(category_id).update(kwargs)
        return True

    @classmethod
    async def delete(cls, category_id: str) -> bool:
        await cls.col().document(category_id).delete()
        return True
