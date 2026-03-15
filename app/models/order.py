from datetime import datetime
from typing import Optional
from enum import Enum
from .database import get_db
from google.cloud.firestore_v1.base_query import FieldFilter


class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    DELIVERING = "delivering"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class PaymentStatus(str, Enum):
    UNPAID = "unpaid"
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentMethod(str, Enum):
    PAYME = "payme"
    CLICK = "click"
    CASH = "cash"


class OrderModel:
    collection_name = "orders"

    @classmethod
    def col(cls):
        return get_db().collection(cls.collection_name)

    @classmethod
    async def create(cls, user_id: int, user_name: str,
                     phone: str, address: str,
                     items: list, total: float,
                     payment_method: str = PaymentMethod.CASH,
                     comment: str = "") -> dict:
        import uuid
        # Buyurtma raqami
        agg = await cls.col().count().get()
        count = agg[0][0].value
        order_number = f"ORD-{count + 1:06d}"
        doc_id = str(uuid.uuid4())

        order = {
            "order_number": order_number,
            "user_id": user_id,
            "user_name": user_name,
            "phone": phone,
            "address": address,
            "items": items,
            "total": total,
            "comment": comment,
            "status": OrderStatus.PENDING,
            "payment_method": payment_method,
            "payment_status": PaymentStatus.UNPAID,
            "payment_id": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        await cls.col().document(doc_id).set(order)
        order["id"] = doc_id
        order["_id"] = doc_id
        return order

    @classmethod
    async def get_by_id(cls, order_id: str) -> Optional[dict]:
        doc = await cls.col().document(order_id).get()
        if doc.exists:
            data = doc.to_dict()
            data["id"] = doc.id
            data["_id"] = doc.id
            return data
        return None

    @classmethod
    async def get_by_user(cls, user_id: int,
                           skip: int = 0, limit: int = 10) -> list:
        result = []
        query = cls.col()\
            .where(filter=FieldFilter("user_id", "==", user_id))\
            .order_by("created_at", direction="DESCENDING")\
            .limit(limit + skip)
        async for doc in query.stream():
            data = doc.to_dict()
            data["id"] = doc.id
            data["_id"] = doc.id
            result.append(data)
        return result[skip:]

    @classmethod
    async def get_all(cls, status: Optional[str] = None,
                       skip: int = 0, limit: int = 20) -> list:
        result = []
        if status:
            query = cls.col()\
                .where(filter=FieldFilter("status", "==", status))\
                .order_by("created_at", direction="DESCENDING")\
                .limit(limit + skip)
        else:
            query = cls.col()\
                .order_by("created_at", direction="DESCENDING")\
                .limit(limit + skip)
        async for doc in query.stream():
            data = doc.to_dict()
            data["id"] = doc.id
            data["_id"] = doc.id
            result.append(data)
        return result[skip:]

    @classmethod
    async def count_by_status(cls, status: Optional[str] = None) -> int:
        if status:
            agg = await cls.col().where(filter=FieldFilter("status", "==", status)).count().get()
        else:
            agg = await cls.col().count().get()
        return agg[0][0].value

    @classmethod
    async def update_status(cls, order_id: str, status: str) -> bool:
        await cls.col().document(order_id).update({
            "status": status,
            "updated_at": datetime.utcnow()
        })
        return True

    @classmethod
    async def update_payment(cls, order_id: str, payment_status: str,
                              payment_id: Optional[str] = None) -> bool:
        update = {"payment_status": payment_status, "updated_at": datetime.utcnow()}
        if payment_id:
            update["payment_id"] = payment_id
        await cls.col().document(order_id).update(update)
        return True

    @classmethod
    async def count_pending_receipts(cls) -> int:
        """Chek yuborilgan, lekin tasdiqlanmagan buyurtmalar soni"""
        count = 0
        async for doc in cls.col().stream():
            d = doc.to_dict()
            if d.get("payment_status") == "pending" and d.get("receipt_photo"):
                count += 1
        return count

    @classmethod
    async def get_pending_receipts(cls, limit: int = 20) -> list:
        """Chek yuborilgan, lekin tasdiqlanmagan buyurtmalar"""
        result = []
        async for doc in cls.col().stream():
            d = doc.to_dict()
            if d.get("payment_status") == "pending" and d.get("receipt_photo"):
                d["id"] = doc.id
                d["_id"] = doc.id
                result.append(d)
            if len(result) >= limit:
                break
        return result

    @classmethod
    async def get_statistics(cls) -> dict:
        total_agg = await cls.col().count().get()
        total_orders = total_agg[0][0].value

        paid_agg = await cls.col().where(filter=FieldFilter("payment_status", "==", "paid")).count().get()
        paid_orders = paid_agg[0][0].value

        # Daromad hisoblash
        total_revenue = 0.0
        async for doc in cls.col().where(filter=FieldFilter("payment_status", "==", "paid")).stream():
            total_revenue += doc.to_dict().get("total", 0)

        return {
            "total_orders": total_orders,
            "paid_orders": paid_orders,
            "total_revenue": total_revenue,
        }
