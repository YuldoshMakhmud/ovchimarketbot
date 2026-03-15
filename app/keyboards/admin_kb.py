from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


def admin_main_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="📦 Mahsulotlar"),
        KeyboardButton(text="📁 Kategoriyalar"),
    )
    builder.row(
        KeyboardButton(text="📋 Buyurtmalar"),
        KeyboardButton(text="👥 Foydalanuvchilar"),
    )
    builder.row(
        KeyboardButton(text="📊 Statistika"),
        KeyboardButton(text="📢 Xabar yuborish"),
    )
    builder.row(KeyboardButton(text="🏠 Asosiy menyu"))
    return builder.as_markup(resize_keyboard=True)


def admin_products_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="➕ Mahsulot qo'shish"),
        KeyboardButton(text="📋 Mahsulotlar ro'yxati"),
    )
    builder.row(KeyboardButton(text="⬅️ Admin menyu"))
    return builder.as_markup(resize_keyboard=True)


def admin_categories_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="➕ Kategoriya qo'shish"),
        KeyboardButton(text="📋 Kategoriyalar ro'yxati"),
    )
    builder.row(KeyboardButton(text="⬅️ Admin menyu"))
    return builder.as_markup(resize_keyboard=True)


def admin_orders_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="🕐 Yangi buyurtmalar"),
        KeyboardButton(text="✅ Tasdiqlangan"),
    )
    builder.row(
        KeyboardButton(text="🚚 Yetkazilmoqda"),
        KeyboardButton(text="📦 Barcha buyurtmalar"),
    )
    builder.row(KeyboardButton(text="⬅️ Admin menyu"))
    return builder.as_markup(resize_keyboard=True)


def order_status_kb(order_id: str, current_status: str) -> InlineKeyboardMarkup:
    statuses = [
        ("confirmed", "✅ Tasdiqlash"),
        ("preparing", "👨‍🍳 Tayyorlanmoqda"),
        ("delivering", "🚚 Yetkazilmoqda"),
        ("delivered", "📦 Yetkazildi"),
        ("cancelled", "❌ Bekor qilish"),
    ]
    builder = InlineKeyboardBuilder()
    for status_key, status_text in statuses:
        if status_key != current_status:
            builder.button(
                text=status_text,
                callback_data=f"order_status_{order_id}_{status_key}"
            )
    builder.adjust(2)
    return builder.as_markup()


def product_manage_kb(product_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Tahrirlash", callback_data=f"admin_edit_prod_{product_id}")
    builder.button(text="🗑 O'chirish", callback_data=f"admin_del_prod_{product_id}")
    builder.button(
        text="🚫 Faolsizlashtirish" if True else "✅ Faollashtirish",
        callback_data=f"admin_toggle_prod_{product_id}"
    )
    builder.adjust(2)
    return builder.as_markup()


def category_manage_kb(category_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Tahrirlash", callback_data=f"admin_edit_cat_{category_id}")
    builder.button(text="🗑 O'chirish", callback_data=f"admin_del_cat_{category_id}")
    builder.adjust(2)
    return builder.as_markup()


def admin_orders_list_kb(orders: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    status_emoji = {
        "pending": "🕐", "confirmed": "✅",
        "preparing": "👨‍🍳", "delivering": "🚚",
        "delivered": "📦", "cancelled": "❌",
    }
    for order in orders:
        emoji = status_emoji.get(order.get("status", ""), "📋")
        builder.button(
            text=f"{emoji} {order['order_number']} | {order['user_name'][:15]}",
            callback_data=f"admin_order_{str(order['_id'])}"
        )
    builder.adjust(1)
    return builder.as_markup()


def cancel_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="❌ Bekor qilish"))
    return builder.as_markup(resize_keyboard=True)


def receipt_confirm_kb(order_id: str) -> InlineKeyboardMarkup:
    """Chek rasmini tasdiqlash yoki rad etish tugmalari"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ Tasdiqlash",
        callback_data=f"receipt_approve_{order_id}"
    )
    builder.button(
        text="❌ Rad etish",
        callback_data=f"receipt_reject_{order_id}"
    )
    builder.button(
        text="📋 Buyurtmani ko'rish",
        callback_data=f"admin_order_{order_id}"
    )
    builder.adjust(2, 1)
    return builder.as_markup()


def admin_orders_kb_with_receipts() -> ReplyKeyboardMarkup:
    """Buyurtmalar menyusi + kutayotgan cheklar"""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="🧾 Kutayotgan cheklar"),
        KeyboardButton(text="🕐 Yangi buyurtmalar"),
    )
    builder.row(
        KeyboardButton(text="✅ Tasdiqlangan"),
        KeyboardButton(text="🚚 Yetkazilmoqda"),
    )
    builder.row(KeyboardButton(text="📦 Barcha buyurtmalar"))
    builder.row(KeyboardButton(text="⬅️ Admin menyu"))
    return builder.as_markup(resize_keyboard=True)
