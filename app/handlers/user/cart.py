from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from app.keyboards import cart_kb, main_menu_kb
from app.models import CartModel
from app.utils import format_price
from app.utils.helpers import format_cart
from config import settings

router = Router()


@router.message(F.text == "🛒 Savat")
async def cart_handler(message: Message):
    cart = await CartModel.get_cart(message.from_user.id)

    if not cart or not cart.get("items"):
        await message.answer(
            "🛒 Savatingiz bo'sh.\n\n"
            "Mahsulot qo'shish uchun <b>Katalog</b>ga o'ting.",
            reply_markup=main_menu_kb(),
            parse_mode="HTML"
        )
        return

    total, count = await CartModel.get_total(message.from_user.id)
    text = format_cart(cart)

    if total < settings.MIN_ORDER_AMOUNT:
        text += (
            f"\n\n⚠️ Minimal buyurtma summasi: "
            f"<b>{format_price(settings.MIN_ORDER_AMOUNT)}</b>"
        )

    await message.answer(
        text,
        reply_markup=cart_kb(cart["items"]),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("cart_plus_"))
async def cart_increase(callback: CallbackQuery):
    product_id = callback.data.replace("cart_plus_", "")
    cart = await CartModel.get_cart(callback.from_user.id)

    if not cart:
        await callback.answer("Savat bo'sh", show_alert=True)
        return

    item = next((i for i in cart["items"] if i["product_id"] == product_id), None)
    if not item:
        await callback.answer("Mahsulot topilmadi", show_alert=True)
        return

    await CartModel.update_quantity(
        callback.from_user.id, product_id, item["quantity"] + 1
    )
    await _update_cart_message(callback)


@router.callback_query(F.data.startswith("cart_minus_"))
async def cart_decrease(callback: CallbackQuery):
    product_id = callback.data.replace("cart_minus_", "")
    cart = await CartModel.get_cart(callback.from_user.id)

    if not cart:
        await callback.answer("Savat bo'sh", show_alert=True)
        return

    item = next((i for i in cart["items"] if i["product_id"] == product_id), None)
    if not item:
        await callback.answer("Mahsulot topilmadi", show_alert=True)
        return

    new_qty = item["quantity"] - 1
    await CartModel.update_quantity(callback.from_user.id, product_id, new_qty)
    await _update_cart_message(callback)


@router.callback_query(F.data.startswith("cart_del_"))
async def cart_delete_item(callback: CallbackQuery):
    product_id = callback.data.replace("cart_del_", "")
    await CartModel.remove_item(callback.from_user.id, product_id)
    await callback.answer("🗑 Mahsulot o'chirildi")
    await _update_cart_message(callback)


@router.callback_query(F.data == "cart_clear")
async def cart_clear(callback: CallbackQuery):
    await CartModel.clear_cart(callback.from_user.id)
    await callback.message.edit_text(
        "🛒 Savat tozalandi!\n\nMahsulot qo'shish uchun Katalogga o'ting."
    )
    await callback.answer("✅ Savat tozalandi")


async def _update_cart_message(callback: CallbackQuery):
    cart = await CartModel.get_cart(callback.from_user.id)

    if not cart or not cart.get("items"):
        await callback.message.edit_text(
            "🛒 Savatingiz bo'sh."
        )
        return

    text = format_cart(cart)
    total, _ = await CartModel.get_total(callback.from_user.id)

    if total < settings.MIN_ORDER_AMOUNT:
        text += (
            f"\n\n⚠️ Minimal buyurtma summasi: "
            f"<b>{format_price(settings.MIN_ORDER_AMOUNT)}</b>"
        )

    try:
        await callback.message.edit_text(
            text,
            reply_markup=cart_kb(cart["items"]),
            parse_mode="HTML"
        )
    except Exception:
        pass
    await callback.answer()
