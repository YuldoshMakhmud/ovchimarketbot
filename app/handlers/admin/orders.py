from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from app.keyboards import admin_orders_kb
from app.keyboards.admin_kb import (
    order_status_kb, admin_orders_list_kb,
    receipt_confirm_kb, admin_orders_kb_with_receipts
)
from app.models import OrderModel
from app.utils import is_admin, format_price
from app.utils.helpers import format_order

router = Router()


def admin_filter(message: Message) -> bool:
    return is_admin(message.from_user.id)


@router.message(F.text == "📋 Buyurtmalar", admin_filter)
async def orders_menu(message: Message):
    pending_count = await OrderModel.count_by_status("pending")
    # To'lov kutayotganlar (chek yuborilgan, tasdiqlanmagan)
    receipt_count = await OrderModel.count_pending_receipts()

    await message.answer(
        f"📋 <b>Buyurtmalar boshqaruvi</b>\n\n"
        f"🕐 Yangi buyurtmalar: <b>{pending_count}</b>\n"
        f"🧾 Chek kutayotgan: <b>{receipt_count}</b>",
        reply_markup=admin_orders_kb_with_receipts(),
        parse_mode="HTML"
    )


@router.message(F.text == "🧾 Kutayotgan cheklar", admin_filter)
async def pending_receipts(message: Message):
    """To'lov cheki yuborilgan, lekin tasdiqlanmagan buyurtmalar"""
    orders = await OrderModel.get_pending_receipts(limit=20)

    if not orders:
        await message.answer("🧾 Hozircha kutayotgan cheklar yo'q.")
        return

    await message.answer(
        f"🧾 <b>Chek kutayotgan buyurtmalar ({len(orders)} ta):</b>\n\n"
        f"Chekni ko'rish uchun buyurtmani tanlang:",
        reply_markup=admin_orders_list_kb(orders)
    )


@router.message(F.text == "🕐 Yangi buyurtmalar", admin_filter)
async def new_orders(message: Message):
    orders = await OrderModel.get_all(status="pending", limit=20)
    await _send_orders_list(message, orders, "🕐 Yangi buyurtmalar")


@router.message(F.text == "✅ Tasdiqlangan", admin_filter)
async def confirmed_orders(message: Message):
    orders = await OrderModel.get_all(status="confirmed", limit=20)
    await _send_orders_list(message, orders, "✅ Tasdiqlangan buyurtmalar")


@router.message(F.text == "🚚 Yetkazilmoqda", admin_filter)
async def delivering_orders(message: Message):
    orders = await OrderModel.get_all(status="delivering", limit=20)
    await _send_orders_list(message, orders, "🚚 Yetkazilmoqda")


@router.message(F.text == "📦 Barcha buyurtmalar", admin_filter)
async def all_orders(message: Message):
    orders = await OrderModel.get_all(limit=20)
    await _send_orders_list(message, orders, "📦 Barcha buyurtmalar")


async def _send_orders_list(message: Message, orders: list, title: str):
    if not orders:
        await message.answer(f"{title}: yo'q")
        return

    await message.answer(
        f"{title} ({len(orders)} ta):",
        reply_markup=admin_orders_list_kb(orders)
    )


@router.callback_query(F.data.startswith("admin_order_"))
async def order_detail(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q!", show_alert=True)
        return

    order_id = callback.data.replace("admin_order_", "")
    order = await OrderModel.get_by_id(order_id)

    if not order:
        await callback.answer("Buyurtma topilmadi", show_alert=True)
        return

    text = format_order(order)

    # Chek rasmi bormi?
    receipt_photo = order.get("receipt_photo")
    payment_status = order.get("payment_status", "unpaid")

    if receipt_photo and payment_status == "pending":
        # Chek bor — tasdiqlash tugmalari bilan ko'rsat
        try:
            await callback.message.answer_photo(
                photo=receipt_photo,
                caption=f"🧾 <b>To'lov cheki</b>\n\n{text}\n\nChekni tasdiqlaysizmi?",
                reply_markup=receipt_confirm_kb(order_id),
                parse_mode="HTML"
            )
            await callback.answer()
        except Exception:
            await callback.message.edit_text(
                text,
                reply_markup=order_status_kb(order_id, order.get("status", "")),
                parse_mode="HTML"
            )
    else:
        await callback.message.edit_text(
            text,
            reply_markup=order_status_kb(order_id, order.get("status", "")),
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("order_status_"))
async def change_order_status(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q!", show_alert=True)
        return

    parts = callback.data.split("_")
    # order_status_{order_id}_{status}
    order_id = parts[2]
    new_status = parts[3]

    updated = await OrderModel.update_status(order_id, new_status)

    if updated:
        status_map = {
            "confirmed": "✅ Tasdiqlandi",
            "preparing": "👨‍🍳 Tayyorlanmoqda",
            "delivering": "🚚 Yetkazilmoqda",
            "delivered": "📦 Yetkazildi",
            "cancelled": "❌ Bekor qilindi",
        }
        await callback.answer(f"{status_map.get(new_status, 'Yangilandi')}")

        # Yangilangan buyurtmani ko'rsatish
        order = await OrderModel.get_by_id(order_id)
        if order:
            try:
                await callback.message.edit_text(
                    format_order(order),
                    reply_markup=order_status_kb(order_id, new_status),
                    parse_mode="HTML"
                )
            except Exception:
                pass

            # Mijozga xabar yuborish
            status_text_for_user = {
                "confirmed": "✅ Buyurtmangiz tasdiqlandi!",
                "preparing": "👨‍🍳 Buyurtmangiz tayyorlanmoqda...",
                "delivering": "🚚 Buyurtmangiz yetkazilmoqda!",
                "delivered": "📦 Buyurtmangiz yetkazildi! Xarid qilganingiz uchun rahmat! 🎉",
                "cancelled": "❌ Buyurtmangiz bekor qilindi. Muammolar uchun admin bilan bog'laning.",
            }
            if new_status in status_text_for_user:
                try:
                    await callback.bot.send_message(
                        order["user_id"],
                        f"{status_text_for_user[new_status]}\n\n"
                        f"📋 Buyurtma: <b>{order['order_number']}</b>",
                        parse_mode="HTML"
                    )
                except Exception:
                    pass
    else:
        await callback.answer("❌ Yangilashda xato", show_alert=True)
