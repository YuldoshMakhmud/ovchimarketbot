from aiogram import Router, F
from aiogram.types import Message
from app.keyboards import main_menu_kb, contact_kb
from app.models import UserModel, OrderModel
from app.utils import format_price

router = Router()


@router.message(F.text == "👤 Profil")
async def profile_handler(message: Message, db_user: dict):
    orders = await OrderModel.get_by_user(message.from_user.id, limit=100)
    total_spent = sum(
        o["total"] for o in orders
        if o.get("payment_status") == "paid"
    )

    text = (
        f"👤 <b>Profilingiz</b>\n\n"
        f"👤 Ism: {db_user.get('full_name', 'Noma\'lum')}\n"
        f"📱 Telefon: {db_user.get('phone', 'Ko\'rsatilmagan')}\n"
        f"🔖 Username: @{db_user.get('username', 'yo\'q')}\n\n"
        f"📦 Jami buyurtmalar: {len(orders)} ta\n"
        f"💰 Jami xarid: {format_price(total_spent)}\n"
    )

    await message.answer(text, reply_markup=main_menu_kb(), parse_mode="HTML")
