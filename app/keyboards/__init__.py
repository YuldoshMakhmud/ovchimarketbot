from .user_kb import (
    main_menu_kb, catalog_kb, product_kb,
    cart_kb, checkout_kb, contact_kb,
    payment_method_kb, back_kb, confirm_kb
)
from .admin_kb import (
    admin_main_kb, admin_products_kb, admin_orders_kb,
    admin_categories_kb, order_status_kb
)

__all__ = [
    "main_menu_kb", "catalog_kb", "product_kb",
    "cart_kb", "checkout_kb", "contact_kb",
    "payment_method_kb", "back_kb", "confirm_kb",
    "admin_main_kb", "admin_products_kb", "admin_orders_kb",
    "admin_categories_kb", "order_status_kb"
]
