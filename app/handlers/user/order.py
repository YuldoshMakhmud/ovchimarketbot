import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from app.keyboards import main_menu_kb, payment_method_kb, confirm_kb
from app.keyboards.user_kb import orders_list_kb
from app.models import CartModel, OrderModel, UserModel
from app.utils import format_price
from app.utils.helpers import format_order
from config import settings

router = Router()
logger = logging.getLogger(__name__)


class OrderState(StatesGroup):
    waiting_phone = State()
    waiting_address = State()
    waiting_comment = State()
    waiting_confirm = State()


# ──────────────────────────────────────────────────────────────────────────────
# Buyurtma boshlash — savatdan
# ──────────────────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "checkout")
async def checkout_start(callback: CallbackQuery, state: FSMContext):
    cart = await CartModel.get_cart(callback.from_user.id)

    if not cart or not cart.get("items"):
        await callback.answer("🛒 Savat bo'sh!", show_alert=True)
        return

    total, count = await CartModel.get_total(callback.from_user.id)

    if total < settings.MIN_ORDER_AMOUNT:
        await callback.answer(
            f"⚠️ Minimal buyurtma summasi: {format_price(settings.MIN_ORDER_AMOUNT)}",
            show_alert=True
        )
        return

    user = await UserModel.get_by_telegram_id(callback.from_user.id)
    await state.update_data(cart=cart, total=total)
    await callback.answer()

    if user and user.get("phone"):
        await state.update_data(phone=user["phone"])
        await callback.message.answer(
            "📍 Yetkazib berish manzilini kiriting:\n"
            "(Shahar, ko'cha, uy raqami)"
        )
        await state.set_state(OrderState.waiting_address)
    else:
        await callback.message.answer(
            "📱 Telefon raqamingizni kiriting:\n"
            "Masalan: +998901234567"
        )
        await state.set_state(OrderState.waiting_phone)


# Telefon
@router.message(OrderState.waiting_phone)
async def process_phone(message: Message, state: FSMContext):
    phone = message.text.strip()
    if not phone.startswith("+") or len(phone) < 10:
        await message.answer(
            "❌ Noto'g'ri format. Masalan: +998901234567"
        )
        return
    await UserModel.update_phone(message.from_user.id, phone)
    await state.update_data(phone=phone)
    await message.answer("📍 Yetkazib berish manzilini kiriting:")
    await state.set_state(OrderState.waiting_address)


# Manzil
@router.message(OrderState.waiting_address)
async def process_address(message: Message, state: FSMContext):
    address = message.text.strip()
    if len(address) < 5:
        await message.answer("❌ Manzil juda qisqa. To'liq manzil kiriting.")
        return
    await state.update_data(address=address)
    await message.answer(
        "💬 Qo'shimcha izoh (ixtiyoriy):\n"
        "Yoki /skip yuboring"
    )
    await state.set_state(OrderState.waiting_comment)


# Izoh
@router.message(OrderState.waiting_comment)
async def process_comment(message: Message, state: FSMContext):
    comment = "" if message.text in ("/skip", "o'tkazib yuborish", "-") else message.text.strip()
    await state.update_data(comment=comment)

    data = await state.get_data()
    cart = data["cart"]
    total = data["total"]
    phone = data["phone"]
    address = data["address"]

    items_text = "\n".join(
        f"  • {item['product_name']} x{item['quantity']} = "
        f"{format_price(item['price'] * item['quantity'])}"
        for item in cart["items"]
    )

    confirm_text = (
        f"📋 <b>Buyurtmangizni tasdiqlang:</b>\n\n"
        f"🛍 Mahsulotlar:\n{items_text}\n\n"
        f"💰 Jami: <b>{format_price(total)}</b>\n"
        f"📍 Manzil: {address}\n"
        f"📱 Telefon: {phone}\n"
    )
    if comment:
        confirm_text += f"💬 Izoh: {comment}\n"

    await message.answer(
        confirm_text,
        reply_markup=confirm_kb("confirm_order_yes", "confirm_order_no"),
        parse_mode="HTML"
    )
    await state.set_state(OrderState.waiting_confirm)


# Buyurtmani bekor qilish
@router.callback_query(F.data == "confirm_order_no", OrderState.waiting_confirm)
async def cancel_checkout(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Buyurtma bekor qilindi.")
    await callback.message.answer("Asosiy menyuga qaytdingiz.", reply_markup=main_menu_kb())


# ──────────────────────────────────────────────────────────────────────────────
# Buyurtmani tasdiqlash → chek yuborish sahifasiga o'tish
# ──────────────────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "confirm_order_yes", OrderState.waiting_confirm)
async def confirm_checkout(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    cart = data["cart"]
    total = data["total"]
    phone = data["phone"]
    address = data["address"]
    comment = data.get("comment", "")

    # Buyurtma yaratish
    order = await OrderModel.create(
        user_id=callback.from_user.id,
        user_name=callback.from_user.full_name,
        phone=phone,
        address=address,
        items=cart["items"],
        total=total,
        comment=comment,
    )

    await CartModel.clear_cart(callback.from_user.id)
    await state.clear()

    order_id = str(order["_id"])

    # Foydalanuvchiga chek yuborish tugmasi
    await callback.message.edit_text(
        f"✅ <b>Buyurtmangiz qabul qilindi!</b>\n\n"
        f"📋 Buyurtma raqami: <b>{order['order_number']}</b>\n"
        f"💰 Jami: <b>{format_price(total)}</b>\n\n"
        f"Endi to'lov qilib, chek rasmini yuboring 👇",
        reply_markup=payment_method_kb(order_id),
        parse_mode="HTML"
    )

    # Adminlarga yangi buyurtma haqida xabar
    await notify_admins_new_order(callback.bot, order, callback.from_user)


async def notify_admins_new_order(bot, order: dict, from_user):
    username = f"@{from_user.username}" if from_user.username else "yo'q"
    text = (
        f"🆕 <b>Yangi buyurtma!</b>\n\n"
        f"👤 {from_user.full_name} ({username})\n"
        f"📋 {order['order_number']}\n"
        f"💰 {format_price(order['total'])}\n"
        f"📍 {order['address']}\n"
        f"📱 {order['phone']}\n\n"
        f"⏳ Chek kutilmoqda..."
    )
    for admin_id in settings.admin_ids_list:
        try:
            await bot.send_message(admin_id, text, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Admin {admin_id} ga yangi buyurtma xabari xatosi: {e}")


# ──────────────────────────────────────────────────────────────────────────────
# Buyurtmalarim
# ──────────────────────────────────────────────────────────────────────────────

@router.message(F.text == "📦 Buyurtmalarim")
async def my_orders(message: Message):
    orders = await OrderModel.get_by_user(message.from_user.id, limit=10)

    if not orders:
        await message.answer(
            "📦 Sizda hali buyurtmalar yo'q.\n\n"
            "Buyurtma berish uchun <b>Katalog</b>ga o'ting.",
            parse_mode="HTML"
        )
        return

    await message.answer(
        f"📦 <b>Buyurtmalaringiz ({len(orders)} ta):</b>",
        reply_markup=orders_list_kb(orders),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("order_detail_"))
async def order_detail(callback: CallbackQuery):
    order_id = callback.data.replace("order_detail_", "")
    order = await OrderModel.get_by_id(order_id)

    if not order or order["user_id"] != callback.from_user.id:
        await callback.answer("Buyurtma topilmadi", show_alert=True)
        return

    await callback.message.edit_text(
        format_order(order),
        parse_mode="HTML"
    )
