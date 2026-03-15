from aiogram import Router
from .start import router as start_router
from .catalog import router as catalog_router
from .cart import router as cart_router
from .order import router as order_router
from .profile import router as profile_router
from .payment import router as payment_router

user_router = Router()
user_router.include_router(start_router)
user_router.include_router(catalog_router)
user_router.include_router(cart_router)
user_router.include_router(order_router)
user_router.include_router(profile_router)
user_router.include_router(payment_router)

__all__ = ["user_router"]
