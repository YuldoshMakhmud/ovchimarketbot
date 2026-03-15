import base64
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from app.keyboards import catalog_kb, main_menu_kb
from app.keyboards.user_kb import product_list_kb, product_kb
from app.models import CategoryModel, ProductModel, CartModel
from app.utils import format_price


def get_photo_input(photo_data):
    """Base64 yoki URL rasmni Telegram uchun tayyorlash"""
    if not photo_data:
        return None
    if photo_data.startswith("http"):
        return photo_data  # URL — to'g'ri ishlatsa bo'ladi
    # Base64 string
    try:
        img_bytes = base64.b64decode(photo_data)
        return BufferedInputFile(img_bytes, filename="photo.jpg")
    except Exception:
        return None

router = Router()

PER_PAGE = 8


@router.message(F.text == "🛍 Katalog")
async def catalog_handler(message: Message):
    categories = await CategoryModel.get_all_active()

    if not categories:
        await message.answer("😕 Hozircha mahsulotlar yo'q.")
        return

    await message.answer(
        "🛍 <b>Kategoriyalarni tanlang:</b>",
        reply_markup=catalog_kb(categories),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "back_to_catalog")
async def back_to_catalog(callback: CallbackQuery):
    categories = await CategoryModel.get_all_active()
    if not categories:
        await callback.answer("Kategoriyalar yo'q", show_alert=True)
        return
    await callback.message.edit_text(
        "🛍 <b>Kategoriyalarni tanlang:</b>",
        reply_markup=catalog_kb(categories),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("cat_"))
async def category_products(callback: CallbackQuery):
    data = callback.data  # cat_<id> yoki cat_<id>_p<page>
    parts = data.split("_")

    # "cat_<id>" yoki "cat_<id>_p<page>"
    if len(parts) == 2:
        category_id = parts[1]
        page = 0
    elif len(parts) == 3 and parts[2].startswith("p"):
        category_id = parts[1]
        page = int(parts[2][1:])
    else:
        await callback.answer("Noto'g'ri so'rov")
        return

    category = await CategoryModel.get_by_id(category_id)
    if not category:
        await callback.answer("Kategoriya topilmadi", show_alert=True)
        return

    cat_name = category.get("name", "")
    total = await ProductModel.count_by_category(category_id, category_name=cat_name)
    products = await ProductModel.get_by_category(
        category_id, skip=page * PER_PAGE, limit=PER_PAGE, category_name=cat_name
    )

    if not products:
        await callback.answer(
            "Bu kategoriyada mahsulotlar yo'q", show_alert=True
        )
        return

    await callback.message.edit_text(
        f"📁 <b>{category['name']}</b>\n"
        f"📦 Jami: {total} ta mahsulot\n\n"
        f"Mahsulotni tanlang:",
        reply_markup=product_list_kb(products, category_id, page, total, PER_PAGE),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("prod_"))
async def product_detail(callback: CallbackQuery):
    product_id = callback.data.split("_")[1]
    product = await ProductModel.get_by_id(product_id)

    if not product:
        await callback.answer("Mahsulot topilmadi", show_alert=True)
        return

    stock_text = ""
    if product.get("stock", 0) <= 0:
        stock_text = "\n⚠️ <i>Omborda yo'q</i>"
    elif product.get("stock", 0) <= 5:
        stock_text = f"\n⚠️ Faqat {product['stock']} ta qoldi"

    text = (
        f"🛍 <b>{product['name']}</b>\n\n"
        f"📝 {product.get('description', 'Tavsif yo\'q')}\n\n"
        f"💰 Narxi: <b>{format_price(product['price'])}</b>\n"
        f"📦 Birlik: {product.get('unit', 'dona')}"
        f"{stock_text}"
    )

    photo = get_photo_input(product.get("photo") or product.get("image"))
    if photo:
        await callback.message.answer_photo(
            photo=photo,
            caption=text,
            reply_markup=product_kb(product_id),
            parse_mode="HTML"
        )
        await callback.message.delete()
    else:
        await callback.message.edit_text(
            text,
            reply_markup=product_kb(product_id),
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("qty_"))
async def quantity_change(callback: CallbackQuery):
    parts = callback.data.split("_")
    action = parts[1]  # minus yoki plus
    product_id = parts[2]

    # Joriy miqdorni inline_keyboard dan olish
    current_qty = 1
    if callback.message.reply_markup:
        for row in callback.message.reply_markup.inline_keyboard:
            for btn in row:
                if btn.callback_data and btn.callback_data.startswith("qty_show_"):
                    try:
                        current_qty = int(btn.text.split()[0])
                    except (ValueError, IndexError):
                        current_qty = 1

    if action == "minus":
        current_qty = max(1, current_qty - 1)
    elif action == "plus":
        current_qty = min(99, current_qty + 1)

    await callback.message.edit_reply_markup(
        reply_markup=product_kb(product_id, current_qty)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("add_cart_"))
async def add_to_cart(callback: CallbackQuery):
    parts = callback.data.split("_")
    product_id = parts[2]
    quantity = int(parts[3]) if len(parts) > 3 else 1

    product = await ProductModel.get_by_id(product_id)
    if not product:
        await callback.answer("Mahsulot topilmadi", show_alert=True)
        return

    if product.get("stock", 0) <= 0:
        await callback.answer("❌ Bu mahsulot omborda yo'q!", show_alert=True)
        return

    await CartModel.add_item(
        user_id=callback.from_user.id,
        product_id=product_id,
        product_name=product["name"],
        price=product["price"],
        quantity=quantity
    )

    total, count = await CartModel.get_total(callback.from_user.id)
    await callback.answer(
        f"✅ Savatga qo'shildi!\n"
        f"🛒 Savat: {count} ta | {format_price(total)}",
        show_alert=True
    )


@router.callback_query(F.data == "back_to_products")
async def back_to_products(callback: CallbackQuery):
    await callback.answer()
    await callback.message.delete()
