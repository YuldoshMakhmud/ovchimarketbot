from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


def main_menu_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="🛍 Katalog"),
        KeyboardButton(text="🛒 Savat"),
    )
    builder.row(
        KeyboardButton(text="📦 Buyurtmalarim"),
        KeyboardButton(text="👤 Profil"),
    )
    builder.row(
        KeyboardButton(text="📞 Aloqa"),
        KeyboardButton(text="ℹ️ Haqida"),
    )
    return builder.as_markup(resize_keyboard=True)


def contact_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="📱 Telefon raqamni yuborish",
                       request_contact=True)
    )
    builder.row(KeyboardButton(text="⬅️ Orqaga"))
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


def back_kb(text: str = "⬅️ Orqaga") -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text=text))
    return builder.as_markup(resize_keyboard=True)


def catalog_kb(categories: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(
            text=cat["name"],
            callback_data=f"cat_{str(cat['_id'])}"
        )
    builder.adjust(2)
    return builder.as_markup()


def product_list_kb(products: list, category_id: str,
                     page: int = 0, total: int = 0,
                     per_page: int = 10) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for prod in products:
        builder.button(
            text=f"{prod['name']} - {prod['price']:,.0f} so'm",
            callback_data=f"prod_{str(prod['_id'])}"
        )
    builder.adjust(1)

    # Sahifalash
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(
            text="◀️ Oldingi",
            callback_data=f"cat_{category_id}_p{page - 1}"
        ))
    if (page + 1) * per_page < total:
        nav_buttons.append(InlineKeyboardButton(
            text="Keyingi ▶️",
            callback_data=f"cat_{category_id}_p{page + 1}"
        ))
    if nav_buttons:
        builder.row(*nav_buttons)

    builder.row(InlineKeyboardButton(
        text="⬅️ Kategoriyalar",
        callback_data="back_to_catalog"
    ))
    return builder.as_markup()


def product_kb(product_id: str, quantity: int = 1) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="➖", callback_data=f"qty_minus_{product_id}"),
        InlineKeyboardButton(text=f"{quantity} dona", callback_data=f"qty_show_{product_id}"),
        InlineKeyboardButton(text="➕", callback_data=f"qty_plus_{product_id}"),
    )
    builder.row(
        InlineKeyboardButton(
            text="🛒 Savatga qo'shish",
            callback_data=f"add_cart_{product_id}_{quantity}"
        )
    )
    builder.row(
        InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_products")
    )
    return builder.as_markup()


def cart_kb(items: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for item in items:
        # Har bir mahsulot uchun miqdor boshqaruvi
        builder.row(
            InlineKeyboardButton(
                text=f"➖ {item['product_name'][:20]}",
                callback_data=f"cart_minus_{item['product_id']}"
            ),
            InlineKeyboardButton(
                text=f"{item['quantity']}",
                callback_data=f"cart_qty_{item['product_id']}"
            ),
            InlineKeyboardButton(
                text="➕",
                callback_data=f"cart_plus_{item['product_id']}"
            ),
            InlineKeyboardButton(
                text="🗑",
                callback_data=f"cart_del_{item['product_id']}"
            ),
        )
    builder.row(
        InlineKeyboardButton(text="🗑 Savatni tozalash", callback_data="cart_clear")
    )
    builder.row(
        InlineKeyboardButton(text="✅ Buyurtma berish", callback_data="checkout")
    )
    return builder.as_markup()


def checkout_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Tasdiqlash", callback_data="confirm_order")
    builder.button(text="✏️ Manzilni o'zgartirish", callback_data="change_address")
    builder.button(text="❌ Bekor qilish", callback_data="cancel_order")
    builder.adjust(1)
    return builder.as_markup()


def payment_method_kb(order_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🧾 Chek rasmini yuborish",
        callback_data=f"pay_receipt_{order_id}"
    )
    builder.adjust(1)
    return builder.as_markup()


def confirm_kb(yes_data: str, no_data: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Ha", callback_data=yes_data)
    builder.button(text="❌ Yo'q", callback_data=no_data)
    return builder.as_markup()


def orders_list_kb(orders: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for order in orders:
        status_emoji = {
            "pending": "🕐",
            "confirmed": "✅",
            "preparing": "👨‍🍳",
            "delivering": "🚚",
            "delivered": "📦",
            "cancelled": "❌",
        }.get(order.get("status", ""), "📋")
        builder.button(
            text=f"{status_emoji} {order['order_number']} - {order['total']:,.0f} so'm",
            callback_data=f"order_detail_{str(order['_id'])}"
        )
    builder.adjust(1)
    return builder.as_markup()
