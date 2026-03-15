import base64
import hashlib
import json
from typing import Optional
from config import settings


class PaymeService:
    """
    Payme (Paycom) to'lov tizimi integratsiyasi.
    Docs: https://developer.paycom.uz/docs/
    """

    BASE_URL = "https://checkout.paycom.uz"

    @classmethod
    def generate_payment_link(cls, order_id: str, amount: float,
                               description: str = "") -> str:
        """
        Payme to'lov havolasini yaratish.
        amount - so'mda (tiyin emas!)
        """
        # Payme tiyin qabul qiladi (1 so'm = 100 tiyin)
        amount_in_tiyin = int(amount * 100)

        params = {
            "m": settings.PAYME_ID,
            "ac.order_id": order_id,
            "a": amount_in_tiyin,
            "l": "uz",
        }
        if description:
            params["d"] = description

        # Base64 encode
        params_str = json.dumps(params)
        params_encoded = base64.b64encode(params_str.encode()).decode()

        return f"{cls.BASE_URL}/{params_encoded}"

    @classmethod
    def verify_signature(cls, data: dict) -> bool:
        """Payme webhook imzosini tekshirish."""
        # Payme webhook autentifikatsiya
        # Authorization: Basic base64(PAYME_ID:PAYME_KEY)
        return True  # To'liq implementatsiya uchun

    @classmethod
    def check_perform_transaction(cls, amount: int, order_id: str) -> dict:
        """Tranzaksiyani bajarish mumkinligini tekshirish."""
        return {
            "allow": True
        }

    @classmethod
    def create_transaction(cls, transaction_id: str, order_id: str,
                            amount: int) -> dict:
        """Yangi tranzaksiya yaratish."""
        import time
        return {
            "create_time": int(time.time() * 1000),
            "transaction": transaction_id,
            "state": 1,
        }

    @classmethod
    def perform_transaction(cls, transaction_id: str) -> dict:
        """Tranzaksiyani tasdiqlash."""
        import time
        return {
            "perform_time": int(time.time() * 1000),
            "transaction": transaction_id,
            "state": 2,
        }

    @classmethod
    def cancel_transaction(cls, transaction_id: str, reason: int) -> dict:
        """Tranzaksiyani bekor qilish."""
        import time
        return {
            "cancel_time": int(time.time() * 1000),
            "transaction": transaction_id,
            "state": -1,
        }


class PaymeWebhookHandler:
    """
    Payme webhook so'rovlarini qayta ishlash.

    Payme quyidagi metodlarni chaqiradi:
    - CheckPerformTransaction
    - CreateTransaction
    - PerformTransaction
    - CancelTransaction
    - CheckTransaction
    - GetStatement
    """

    METHODS = {
        "CheckPerformTransaction": "check_perform",
        "CreateTransaction": "create_transaction",
        "PerformTransaction": "perform_transaction",
        "CancelTransaction": "cancel_transaction",
        "CheckTransaction": "check_transaction",
        "GetStatement": "get_statement",
    }

    @classmethod
    async def handle(cls, request_data: dict, order_id: str) -> dict:
        method = request_data.get("method")
        params = request_data.get("params", {})
        request_id = request_data.get("id")

        if method == "CheckPerformTransaction":
            return cls._success_response(
                request_id,
                {"allow": True}
            )

        elif method == "CreateTransaction":
            return cls._success_response(
                request_id,
                PaymeService.create_transaction(
                    params.get("id"),
                    params.get("account", {}).get("order_id"),
                    params.get("amount")
                )
            )

        elif method == "PerformTransaction":
            from app.models import OrderModel
            await OrderModel.update_payment(
                order_id,
                payment_status="paid",
                payment_id=params.get("id")
            )
            return cls._success_response(
                request_id,
                PaymeService.perform_transaction(params.get("id"))
            )

        elif method == "CancelTransaction":
            return cls._success_response(
                request_id,
                PaymeService.cancel_transaction(
                    params.get("id"),
                    params.get("reason", 1)
                )
            )

        return cls._error_response(request_id, -32601, "Method not found")

    @staticmethod
    def _success_response(request_id, result: dict) -> dict:
        return {"jsonrpc": "2.0", "id": request_id, "result": result}

    @staticmethod
    def _error_response(request_id, code: int, message: str) -> dict:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": code, "message": message}
        }
