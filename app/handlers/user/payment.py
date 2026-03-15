import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from app.models import OrderModel
from app.utils import format_price, is_admin
from app.keyboards import main_menu_kb
from config import settings

router = Router()
logger = logging.getLogger(__name__)


class PaymentState(StatesGroup):
    waiting_receipt = State()  # Chek rasmini kutish


# ──────────────────────────────────────────────────────────────────────────────
# 1. "Chek rasmini yuborish" tugmasi bosiladi
# ──────────────────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("pay_receipt_"))
async def request_receipt(callback: CallbackQuery, state: FSMContext):
    order_id = callback.data.replace("pay_receipt_", "")
    order = await OrderModel.get_by_id(order_id)

    if not order:
        await callback.answer("Buyurtma topilmadi!", show_alert=True)
        return

    await state.update_data(order_id=order_id)
    await state.set_state(PaymentState.waiting_receipt)
    await callback.answer()

    text = (
        f"🧾 <b>To'lov chekini yuboring</b>\n\n"
        f"📋 Buyurtma: <b>{order['order_number']}</b>\n"
        f"💰 Summa: <b>{format_price(order['total'])}</b>\n\n"
        f"1️⃣ Quyidagi kartaga pul o'tkazing:\n"
        f"💳 <code>{settings.CARD_NUMBER}</code>\n"
        f"👤 <b>{settings.CARD_OWNER}</b>\n\n"
        f"2️⃣ To'lov cheki rasmini shu yerga yuboring 👇"
    )

    # Eski xabarni o'zgartir
    try:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=None)
    except Exception:
        # edit ishlamasa yangi xabar yuborish
        await callback.bot.send_message(
            chat_id=callback.from_user.id,
            text=text,
            parse_mode="HTML"
        )


# ──────────────────────────────────────────────────────────────────────────────
# 2. Foydalanuvchi chek rasmini yuboradi
# ──────────────────────────────────────────────────────────────────────────────

@router.message(PaymentState.waiting_receipt, F.photo)
async def receive_receipt(message: Message, state: FSMContext):
    data = await state.get_data()
    order_id = data.get("order_id")

    if not order_id:
        await message.answer("❌ Xatolik. Qaytadan buyurtma bering.")
        await state.clear()
        return

    order = await OrderModel.get_by_id(order_id)
    if not order:
        await message.answer("❌ Buyurtma topilmadi.")
        await state.clear()
        return

    photo_file_id = message.photo[-1].file_id

    # Firestorega yozish
    try:
        await OrderModel.update_payment(
            order_id,
            payment_status="pending",
            payment_id=photo_file_id
        )
        await OrderModel.col().document(order_id).update({
            "receipt_photo": photo_file_id,
            "receipt_from": message.from_user.id,
        })
    except Exception as e:
        logger.error(f"Chek saqlash xatosi: {e}")
        await message.answer("❌ Xatolik yuz berdi. Qayta urinib ko'ring.")
        return

    await state.clear()

    # Foydalanuvchiga javob
    await message.answer(
        f"✅ <b>Chek qabul qilindi!</b>\n\n"
        f"📋 Buyurtma: <b>{order['order_number']}</b>\n\n"
        f"⏳ Admin chekni tekshiradi va buyurtmangizni tasdiqlaydi.\n"
        f"📲 Natija haqida sizga xabar beriladi.",
        reply_markup=main_menu_kb(),
        parse_mode="HTML"
    )

    # Adminlarga bildirishnoma
    await notify_admins_receipt(message.bot, order, message.from_user, photo_file_id)


# ──────────────────────────────────────────────────────────────────────────────
# 3. Rasm emas boshqa narsa yuborildi
# ──────────────────────────────────────────────────────────────────────────────

@router.message(PaymentState.waiting_receipt, ~F.photo)
async def wrong_receipt(message: Message):
    await message.answer(
        "❌ Iltimos, <b>rasm (foto)</b> ko'rinishida chek yuboring.\n"
        "Screenshot yoki kamera orqali olingan rasm bo'lishi kerak.",
        parse_mode="HTML"
    )


# ──────────────────────────────────────────────────────────────────────────────
# 4. Adminlarga chek rasmi + tasdiqlash tugmalari
# ──────────────────────────────────────────────────────────────────────────────

async def notify_admins_receipt(bot, order: dict, from_user, photo_file_id: str):
    from app.keyboards.admin_kb import receipt_confirm_kb

    order_id = str(order["_id"])
    username = f"@{from_user.username}" if from_user.username else "username yo'q"

    caption = (
        f"🧾 <b>Yangi to'lov cheki!</b>\n\n"
        f"👤 {from_user.full_name} ({username})\n"
        f"🆔 <code>{from_user.id}</code>\n"
        f"📋 Buyurtma: <b>{order['order_number']}</b>\n"
        f"💰 Summa: <b>{format_price(order['total'])}</b>\n"
        f"📍 Manzil: {order['address']}\n"
        f"📱 Tel: {order['phone']}\n\n"
        f"Tasdiqlaysizmi?"
    )

    for admin_id in settings.admin_ids_list:
        try:
            await bot.send_photo(
                chat_id=admin_id,
                photo=photo_file_id,
                caption=caption,
                reply_markup=receipt_confirm_kb(order_id),
                parse_mode="HTML"
            )
            logger.info(f"✅ Admin {admin_id} ga chek yuborildi")
        except Exception as e:
            logger.error(f"❌ Admin {admin_id} ga yuborishda xato: {e}")


# ──────────────────────────────────────────────────────────────────────────────
# 5. Admin chekni TASDIQLAYDI
# ──────────────────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("receipt_approve_"))
async def approve_receipt(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q!", show_alert=True)
        return

    order_id = callback.data.replace("receipt_approve_", "")
    order = await OrderModel.get_by_id(order_id)
    if not order:
        await callback.answer("Buyurtma topilmadi", show_alert=True)
        return

    await OrderModel.update_payment(order_id, payment_status="paid")
    await OrderModel.update_status(order_id, "confirmed")

    # Admin xabarini yangilash
    try:
        await callback.message.edit_caption(
            caption=(callback.message.caption or "") + "\n\n✅ <b>TASDIQLANDI</b>",
            reply_markup=None,
            parse_mode="HTML"
        )
    except Exception:
        pass

    await callback.answer("✅ Tasdiqlandi!", show_alert=True)

    # Mijozga xabar
    try:
        await callback.bot.send_message(
            chat_id=order["user_id"],
            text=(
                f"✅ <b>To'lovingiz tasdiqlandi!</b>\n\n"
                f"📋 Buyurtma: <b>{order['order_number']}</b>\n"
                f"💰 Summa: <b>{format_price(order['total'])}</b>\n\n"
                f"🚚 Buyurtmangiz tez orada yetkaziladi!\n"
                f"Xarid uchun rahmat 🙏"
            ),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Mijozga tasdiqlash xabari xatosi: {e}")


# ──────────────────────────────────────────────────────────────────────────────
# 6. Admin chekni RAD ETADI
# ──────────────────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("receipt_reject_"))
async def reject_receipt(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q!", show_alert=True)
        return

    order_id = callback.data.replace("receipt_reject_", "")
    order = await OrderModel.get_by_id(order_id)
    if not order:
        await callback.answer("Buyurtma topilmadi", show_alert=True)
        return

    await OrderModel.update_payment(order_id, payment_status="failed")

    try:
        await callback.message.edit_caption(
            caption=(callback.message.caption or "") + "\n\n❌ <b>RAD ETILDI</b>",
            reply_markup=None,
            parse_mode="HTML"
        )
    except Exception:
        pass

    await callback.answer("❌ Rad etildi!", show_alert=True)

    # Mijozga xabar — qayta yuborsin
    try:
        await callback.bot.send_message(
            chat_id=order["user_id"],
            text=(
                f"❌ <b>To'lov cheki tasdiqlanmadi.</b>\n\n"
                f"📋 Buyurtma: <b>{order['order_number']}</b>\n\n"
                f"Iltimos, to'g'ri chekni qayta yuboring.\n"
                f"Savol bo'lsa admin bilan bog'laning."
            ),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Mijozga rad xabari xatosi: {e}")
