from datetime import datetime
from typing import Optional
from .database import get_db


class ProductModel:
    collection_name = "products"

    @classmethod
    def col(cls):
        return get_db().collection(cls.collection_name)

    @classmethod
    def _normalize(cls, data: dict, doc_id: str) -> dict:
        """Firebase ilovasidagi field nomlarini bot formatiga o'tkazish"""
        data["id"] = doc_id
        data["_id"] = doc_id
        # price: new_price yoki price fieldidan olish
        if "price" not in data:
            data["price"] = data.get("new_price") or data.get("old_price") or 0
        # stock: quantity fieldidan
        if "stock" not in data:
            data["stock"] = data.get("quantity", 0)
        # description: desc fieldidan
        if "description" not in data:
            data["description"] = data.get("desc", "")
        # photo: image fieldidan
        if "photo" not in data:
            data["photo"] = data.get("image")
        # is_active: hammasi aktiv (ilovada bu field yo'q)
        data.setdefault("is_active", True)
        # category_id: category (nom) bo'lishi mumkin
        data.setdefault("category_id", data.get("category", ""))
        return data

    @classmethod
    async def create(cls, name: str, price: float, category_id: str,
                     description: str = "", photo: Optional[str] = None,
                     stock: int = 0, unit: str = "dona") -> dict:
        import uuid
        doc_id = str(uuid.uuid4())
        product = {
            "name": name,
            "desc": description,
            "description": description,
            "new_price": price,
            "price": price,
            "category": category_id,
            "category_id": category_id,
            "image": photo,
            "photo": photo,
            "quantity": stock,
            "stock": stock,
            "unit": unit,
            "is_active": True,
            "sold_count": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        await cls.col().document(doc_id).set(product)
        product["id"] = doc_id
        product["_id"] = doc_id
        return product

    @classmethod
    async def get_by_id(cls, product_id: str) -> Optional[dict]:
        doc = await cls.col().document(product_id).get()
        if doc.exists:
            return cls._normalize(doc.to_dict(), doc.id)
        return None

    @classmethod
    async def get_by_category(cls, category_id: str,
                               skip: int = 0, limit: int = 10,
                               category_name: str = "") -> list:
        """category_id (doc ID) yoki category nomi bo'yicha mahsulotlarni olish"""
        result = []
        async for doc in cls.col().stream():
            data = doc.to_dict()
            cat_field = data.get("category", "") or data.get("category_id", "")
            # ID bo'yicha yoki nom bo'yicha moslashtir
            if cat_field == category_id or (category_name and cat_field == category_name):
                result.append(cls._normalize(data, doc.id))
        return result[skip: skip + limit]

    @classmethod
    async def count_by_category(cls, category_id: str, category_name: str = "") -> int:
        count = 0
        async for doc in cls.col().stream():
            data = doc.to_dict()
            cat_field = data.get("category", "") or data.get("category_id", "")
            if cat_field == category_id or (category_name and cat_field == category_name):
                count += 1
        return count

    @classmethod
    async def get_all(cls, skip: int = 0, limit: int = 20) -> list:
        result = []
        async for doc in cls.col().limit(limit + skip).stream():
            result.append(cls._normalize(doc.to_dict(), doc.id))
        return result[skip:]

    @classmethod
    async def count(cls) -> int:
        agg = await cls.col().count().get()
        return agg[0][0].value

    @classmethod
    async def update(cls, product_id: str, **kwargs) -> bool:
        # Bot field nomlarini Firebase field nomlariga ham yozish
        update = dict(kwargs)
        update["updated_at"] = datetime.utcnow()
        if "price" in update:
            update["new_price"] = update["price"]
        if "stock" in update:
            update["quantity"] = update["stock"]
        if "description" in update:
            update["desc"] = update["description"]
        if "photo" in update:
            update["image"] = update["photo"]
        await cls.col().document(product_id).update(update)
        return True

    @classmethod
    async def delete(cls, product_id: str) -> bool:
        await cls.col().document(product_id).delete()
        return True

    @classmethod
    async def search(cls, query: str, limit: int = 10) -> list:
        result = []
        async for doc in cls.col().stream():
            data = doc.to_dict()
            if query.lower() in data.get("name", "").lower():
                result.append(cls._normalize(data, doc.id))
                if len(result) >= limit:
                    break
        return result

    @classmethod
    async def increment_sold(cls, product_id: str, quantity: int = 1):
        from google.cloud.firestore_v1 import transforms
        await cls.col().document(product_id).update({
            "sold_count": transforms.Increment(quantity),
            "quantity": transforms.Increment(-quantity),
            "stock": transforms.Increment(-quantity),
        })
