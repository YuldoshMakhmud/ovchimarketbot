from aiogram import Router
from .main import router as main_router
from .products import router as products_router
from .categories import router as categories_router
from .orders import router as orders_router
from .broadcast import router as broadcast_router

admin_router = Router()
admin_router.include_router(main_router)
admin_router.include_router(products_router)
admin_router.include_router(categories_router)
admin_router.include_router(orders_router)
admin_router.include_router(broadcast_router)

__all__ = ["admin_router"]
