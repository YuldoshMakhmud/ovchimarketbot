import hashlib
import time
from typing import Optional
from config import settings


class ClickService:
    """
    Click to'lov tizimi integratsiyasi.
    Docs: https://docs.click.uz/
    """

    BASE_URL = "https://my.click.uz/services/pay"

    @classmethod
    def generate_payment_link(cls, order_id: str, amount: float,
                               description: str = "") -> str:
        """
        Click to'lov havolasini yaratish.
        amount - so'mda
        """
        params = (
            f"?service_id={settings.CLICK_SERVICE_ID}"
            f"&merchant_id={settings.CLICK_MERCHANT_ID}"
            f"&amount={int(amount)}"
            f"&transaction_param={order_id}"
            f"&return_url=https://t.me/your_bot"
        )
        return f"{cls.BASE_URL}{params}"

    @classmethod
    def verify_prepare_request(cls, data: dict) -> tuple[bool, Optional[str]]:
        """Click prepare so'rovini tekshirish."""
        sign_time = data.get("sign_time", "")
        sign_string = data.get("sign_string", "")
        service_id = data.get("service_id")
        click_trans_id = data.get("click_trans_id")
        merchant_trans_id = data.get("merchant_trans_id")
        amount = data.get("amount")
        action = data.get("action")

        # Imzo tekshirish
        expected_sign = hashlib.md5(
            f"{click_trans_id}{service_id}{settings.CLICK_SECRET_KEY}"
            f"{merchant_trans_id}{amount}{action}{sign_time}".encode()
        ).hexdigest()

        if sign_string != expected_sign:
            return False, "SIGN_CHECK_FAILED"

        return True, None

    @classmethod
    def verify_complete_request(cls, data: dict) -> tuple[bool, Optional[str]]:
        """Click complete so'rovini tekshirish."""
        sign_time = data.get("sign_time", "")
        sign_string = data.get("sign_string", "")
        service_id = data.get("service_id")
        click_trans_id = data.get("click_trans_id")
        merchant_trans_id = data.get("merchant_trans_id")
        merchant_prepare_id = data.get("merchant_prepare_id")
        amount = data.get("amount")
        action = data.get("action")

        expected_sign = hashlib.md5(
            f"{click_trans_id}{service_id}{settings.CLICK_SECRET_KEY}"
            f"{merchant_trans_id}{merchant_prepare_id}{amount}{action}{sign_time}".encode()
        ).hexdigest()

        if sign_string != expected_sign:
            return False, "SIGN_CHECK_FAILED"

        return True, None

    @classmethod
    async def handle_prepare(cls, data: dict) -> dict:
        """Click PREPARE so'rovini qayta ishlash."""
        valid, error = cls.verify_prepare_request(data)
        if not valid:
            return {
                "click_trans_id": data.get("click_trans_id"),
                "merchant_trans_id": data.get("merchant_trans_id"),
                "merchant_prepare_id": None,
                "error": -1,
                "error_note": error or "Sign check failed"
            }

        merchant_trans_id = data.get("merchant_trans_id")  # order_id

        from app.models import OrderModel
        order = await OrderModel.get_by_id(merchant_trans_id)

        if not order:
            return {
                "click_trans_id": data.get("click_trans_id"),
                "merchant_trans_id": merchant_trans_id,
                "merchant_prepare_id": None,
                "error": -5,
                "error_note": "User not found"
            }

        # Summa tekshirish
        expected_amount = int(order["total"])
        received_amount = int(float(data.get("amount", 0)))

        if expected_amount != received_amount:
            return {
                "click_trans_id": data.get("click_trans_id"),
                "merchant_trans_id": merchant_trans_id,
                "merchant_prepare_id": None,
                "error": -2,
                "error_note": "Incorrect parameter amount"
            }

        merchant_prepare_id = int(time.time())
        return {
            "click_trans_id": data.get("click_trans_id"),
            "merchant_trans_id": merchant_trans_id,
            "merchant_prepare_id": merchant_prepare_id,
            "error": 0,
            "error_note": "Success"
        }

    @classmethod
    async def handle_complete(cls, data: dict) -> dict:
        """Click COMPLETE so'rovini qayta ishlash."""
        valid, error = cls.verify_complete_request(data)
        if not valid:
            return {
                "click_trans_id": data.get("click_trans_id"),
                "merchant_trans_id": data.get("merchant_trans_id"),
                "merchant_confirm_id": None,
                "error": -1,
                "error_note": error or "Sign check failed"
            }

        merchant_trans_id = data.get("merchant_trans_id")
        click_trans_id = data.get("click_trans_id")

        from app.models import OrderModel
        order = await OrderModel.get_by_id(merchant_trans_id)

        if not order:
            return {
                "click_trans_id": click_trans_id,
                "merchant_trans_id": merchant_trans_id,
                "merchant_confirm_id": None,
                "error": -5,
                "error_note": "User not found"
            }

        # To'lovni tasdiqlash
        await OrderModel.update_payment(
            merchant_trans_id,
            payment_status="paid",
            payment_id=str(click_trans_id)
        )
        await OrderModel.update_status(merchant_trans_id, "confirmed")

        merchant_confirm_id = int(time.time())
        return {
            "click_trans_id": click_trans_id,
            "merchant_trans_id": merchant_trans_id,
            "merchant_confirm_id": merchant_confirm_id,
            "error": 0,
            "error_note": "Success"
        }
