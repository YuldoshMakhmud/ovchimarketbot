from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from app.keyboards import admin_main_kb, main_menu_kb
from app.models import UserModel, ProductModel, OrderModel
from app.utils import is_admin, format_price

router = Router()


def admin_filter(message: Message) -> bool:
    return is_admin(message.from_user.id)


@router.message(Command("admin"), admin_filter)
async def admin_panel(message: Message):
    stats = await OrderModel.get_statistics()
    user_count = await UserModel.count()
    product_count = await ProductModel.count()

    text = (
        f"🔐 <b>Admin Panel</b>\n\n"
        f"👥 Foydalanuvchilar: {user_count}\n"
        f"📦 Mahsulotlar: {product_count}\n"
        f"📋 Jami buyurtmalar: {stats['total_orders']}\n"
        f"✅ To'langan buyurtmalar: {stats['paid_orders']}\n"
        f"💰 Jami daromad: {format_price(stats['total_revenue'])}\n"
    )

    await message.answer(text, reply_markup=admin_main_kb(), parse_mode="HTML")


@router.message(F.text == "🏠 Asosiy menyu", admin_filter)
async def back_to_main(message: Message):
    await message.answer(
        "Asosiy menyuga qaytdingiz.",
        reply_markup=main_menu_kb()
    )


@router.message(F.text == "📊 Statistika", admin_filter)
async def statistics(message: Message):
    stats = await OrderModel.get_statistics()
    user_count = await UserModel.count()
    product_count = await ProductModel.count()

    pending_count = await OrderModel.count_by_status("pending")
    confirmed_count = await OrderModel.count_by_status("confirmed")
    delivering_count = await OrderModel.count_by_status("delivering")
    delivered_count = await OrderModel.count_by_status("delivered")

    text = (
        f"📊 <b>Statistika</b>\n\n"
        f"👥 Foydalanuvchilar: {user_count}\n"
        f"📦 Mahsulotlar: {product_count}\n\n"
        f"📋 <b>Buyurtmalar:</b>\n"
        f"  🕐 Kutilmoqda: {pending_count}\n"
        f"  ✅ Tasdiqlangan: {confirmed_count}\n"
        f"  🚚 Yetkazilmoqda: {delivering_count}\n"
        f"  📦 Yetkazildi: {delivered_count}\n"
        f"  📊 Jami: {stats['total_orders']}\n\n"
        f"💰 To'langan buyurtmalar: {stats['paid_orders']}\n"
        f"💵 Jami daromad: <b>{format_price(stats['total_revenue'])}</b>"
    )

    await message.answer(text, parse_mode="HTML")
