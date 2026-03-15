from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from app.keyboards import main_menu_kb, contact_kb
from app.models import UserModel
from app.utils import is_admin
from config import settings

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, db_user: dict, is_new_user: bool):
    name = message.from_user.first_name

    if is_new_user:
        text = (
            f"👋 Xush kelibsiz, <b>{name}</b>!\n\n"
            f"🏪 <b>{settings.SHOP_NAME}</b> ga xush kelibsiz!\n\n"
            f"📱 Qulay interfeys orqali mahsulotlarni ko'rib chiqing va "
            f"buyurtma bering."
        )
    else:
        text = (
            f"👋 Qaytib kelganingizdan xursandmiz, <b>{name}</b>!\n\n"
            f"🏪 <b>{settings.SHOP_NAME}</b>"
        )

    await message.answer(text, reply_markup=main_menu_kb(), parse_mode="HTML")

    # Telefon raqami yo'q bo'lsa so'rash
    if not db_user.get("phone"):
        await message.answer(
            "📱 Qulay buyurtma berish uchun telefon raqamingizni ulashing:",
            reply_markup=contact_kb()
        )


@router.message(F.contact)
async def handle_contact(message: Message):
    if message.contact and message.contact.user_id == message.from_user.id:
        phone = message.contact.phone_number
        await UserModel.update_phone(message.from_user.id, phone)
        await message.answer(
            f"✅ Telefon raqamingiz saqlandi: <b>{phone}</b>",
            reply_markup=main_menu_kb(),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            "❌ Iltimos, o'z telefon raqamingizni yuboring.",
            reply_markup=contact_kb()
        )


@router.message(F.text == "ℹ️ Haqida")
async def about_handler(message: Message):
    await message.answer(
        f"ℹ️ <b>{settings.SHOP_NAME}</b> haqida\n\n"
        f"Bu bot orqali siz:\n"
        f"• 🛍 Mahsulotlarni ko'rib chiqishingiz\n"
        f"• 🛒 Savatga qo'shishingiz\n"
        f"• 📦 Buyurtma berishingiz\n"
        f"• 💳 Online to'lov qilishingiz mumkin!\n\n"
        f"💬 Muammolar uchun: @admin",
        parse_mode="HTML"
    )


@router.message(F.text == "📞 Aloqa")
async def contact_handler(message: Message):
    await message.answer(
        "📞 <b>Biz bilan bog'laning:</b>\n\n"
        "📱 Telefon: +998 90 123 45 67\n"
        "💬 Telegram: @shop_support\n"
        "📧 Email: info@shop.uz\n"
        "🕐 Ish vaqti: 9:00 - 22:00",
        parse_mode="HTML"
    )
