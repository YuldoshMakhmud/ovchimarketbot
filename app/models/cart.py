from datetime import datetime
from typing import Optional
from .database import get_db


class CartModel:
    collection_name = "carts"

    @classmethod
    def col(cls):
        return get_db().collection(cls.collection_name)

    @classmethod
    async def get_cart(cls, user_id: int) -> Optional[dict]:
        doc = await cls.col().document(str(user_id)).get()
        if doc.exists:
            data = doc.to_dict()
            data["id"] = doc.id
            return data
        return None

    @classmethod
    async def add_item(cls, user_id: int, product_id: str,
                        product_name: str, price: float, quantity: int = 1):
        cart = await cls.get_cart(user_id)
        if not cart:
            await cls.col().document(str(user_id)).set({
                "user_id": user_id,
                "items": [],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            })
            cart = {"items": []}

        items = cart.get("items", [])
        # Mahsulot borligini tekshirish
        found = False
        for item in items:
            if item["product_id"] == product_id:
                item["quantity"] += quantity
                found = True
                break

        if not found:
            items.append({
                "product_id": product_id,
                "product_name": product_name,
                "price": price,
                "quantity": quantity,
            })

        await cls.col().document(str(user_id)).update({
            "items": items,
            "updated_at": datetime.utcnow()
        })

    @classmethod
    async def remove_item(cls, user_id: int, product_id: str):
        cart = await cls.get_cart(user_id)
        if not cart:
            return
        items = [i for i in cart.get("items", []) if i["product_id"] != product_id]
        await cls.col().document(str(user_id)).update({
            "items": items,
            "updated_at": datetime.utcnow()
        })

    @classmethod
    async def update_quantity(cls, user_id: int, product_id: str, quantity: int):
        if quantity <= 0:
            await cls.remove_item(user_id, product_id)
            return
        cart = await cls.get_cart(user_id)
        if not cart:
            return
        items = cart.get("items", [])
        for item in items:
            if item["product_id"] == product_id:
                item["quantity"] = quantity
                break
        await cls.col().document(str(user_id)).update({
            "items": items,
            "updated_at": datetime.utcnow()
        })

    @classmethod
    async def clear_cart(cls, user_id: int):
        await cls.col().document(str(user_id)).update({
            "items": [],
            "updated_at": datetime.utcnow()
        })

    @classmethod
    async def get_total(cls, user_id: int) -> tuple[float, int]:
        cart = await cls.get_cart(user_id)
        if not cart or not cart.get("items"):
            return 0.0, 0
        total = sum(i["price"] * i["quantity"] for i in cart["items"])
        count = sum(i["quantity"] for i in cart["items"])
        return total, count
