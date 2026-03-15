from config import settings


def format_price(amount: float) -> str:
    return f"{amount:,.0f} {settings.SHOP_CURRENCY}"


def is_admin(user_id: int) -> bool:
    return user_id in settings.admin_ids_list


def format_order(order: dict) -> str:
    status_map = {
        "pending": "🕐 Kutilmoqda",
        "confirmed": "✅ Tasdiqlangan",
        "preparing": "👨‍🍳 Tayyorlanmoqda",
        "delivering": "🚚 Yetkazilmoqda",
        "delivered": "📦 Yetkazildi",
        "cancelled": "❌ Bekor qilindi",
    }
    payment_map = {
        "unpaid": "💳 To'lanmagan",
        "pending": "⏳ Kutilmoqda",
        "paid": "✅ To'langan",
        "failed": "❌ Muvaffaqiyatsiz",
        "refunded": "↩️ Qaytarilgan",
    }
    payment_method_map = {
        "payme": "💳 Payme",
        "click": "💳 Click",
        "cash": "💵 Naqd",
    }

    items_text = "\n".join(
        f"  • {item['product_name']} x{item['quantity']} = "
        f"{format_price(item['price'] * item['quantity'])}"
        for item in order.get("items", [])
    )

    return (
        f"📋 Buyurtma: <b>{order['order_number']}</b>\n"
        f"📅 Sana: {order['created_at'].strftime('%d.%m.%Y %H:%M')}\n"
        f"📊 Holat: {status_map.get(order.get('status', ''), order.get('status', ''))}\n"
        f"💳 To'lov: {payment_method_map.get(order.get('payment_method', ''), '')}\n"
        f"💰 To'lov holati: {payment_map.get(order.get('payment_status', ''), '')}\n\n"
        f"🛍 Mahsulotlar:\n{items_text}\n\n"
        f"📍 Manzil: {order.get('address', '')}\n"
        f"📞 Telefon: {order.get('phone', '')}\n"
        f"💰 Jami: <b>{format_price(order['total'])}</b>"
    )


def format_cart(cart: dict) -> str:
    if not cart or not cart.get("items"):
        return "🛒 Savat bo'sh"

    items_text = "\n".join(
        f"  {i+1}. {item['product_name']}\n"
        f"     {format_price(item['price'])} x {item['quantity']} = "
        f"{format_price(item['price'] * item['quantity'])}"
        for i, item in enumerate(cart["items"])
    )
    total = sum(item["price"] * item["quantity"] for item in cart["items"])
    count = sum(item["quantity"] for item in cart["items"])

    return (
        f"🛒 <b>Savatingiz:</b>\n\n"
        f"{items_text}\n\n"
        f"📦 Jami mahsulotlar: {count} ta\n"
        f"💰 Jami summa: <b>{format_price(total)}</b>"
    )
