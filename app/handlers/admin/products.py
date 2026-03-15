from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from app.keyboards import admin_products_kb
from app.keyboards.admin_kb import cancel_kb, product_manage_kb
from app.keyboards.user_kb import catalog_kb
from app.models import ProductModel, CategoryModel
from app.utils import is_admin, format_price

router = Router()


def admin_filter(message: Message) -> bool:
    return is_admin(message.from_user.id)


class ProductState(StatesGroup):
    waiting_category = State()
    waiting_name = State()
    waiting_description = State()
    waiting_price = State()
    waiting_stock = State()
    waiting_unit = State()
    waiting_photo = State()


@router.message(F.text == "📦 Mahsulotlar", admin_filter)
async def products_menu(message: Message):
    await message.answer(
        "📦 Mahsulotlar boshqaruvi:",
        reply_markup=admin_products_kb()
    )


@router.message(F.text == "📋 Mahsulotlar ro'yxati", admin_filter)
async def products_list(message: Message):
    products = await ProductModel.get_all(limit=20)

    if not products:
        await message.answer("😕 Mahsulotlar yo'q.")
        return

    for prod in products:
        status = "✅" if prod.get("is_active") else "🚫"
        text = (
            f"{status} <b>{prod['name']}</b>\n"
            f"💰 Narxi: {format_price(prod['price'])}\n"
            f"📦 Ombor: {prod.get('stock', 0)} ta\n"
            f"ID: {str(prod['_id'])}"
        )
        await message.answer(
            text,
            reply_markup=product_manage_kb(str(prod["_id"])),
            parse_mode="HTML"
        )


@router.message(F.text == "➕ Mahsulot qo'shish", admin_filter)
async def add_product_start(message: Message, state: FSMContext):
    categories = await CategoryModel.get_all_active()
    if not categories:
        await message.answer(
            "❌ Avval kategoriya qo'shing!",
            reply_markup=admin_products_kb()
        )
        return

    await message.answer(
        "📁 Kategoriyani tanlang:",
        reply_markup=catalog_kb(categories)
    )
    await state.set_state(ProductState.waiting_category)
    await state.update_data(categories=[(str(c["_id"]), c["name"]) for c in categories])


@router.callback_query(F.data.startswith("cat_"), ProductState.waiting_category)
async def process_product_category(callback: CallbackQuery, state: FSMContext):
    category_id = callback.data.split("_")[1]
    category = await CategoryModel.get_by_id(category_id)

    if not category:
        await callback.answer("Kategoriya topilmadi", show_alert=True)
        return

    await state.update_data(category_id=category_id, category_name=category["name"])
    await callback.message.delete()
    await callback.message.answer(
        f"📁 Kategoriya: {category['name']}\n\n"
        f"📝 Mahsulot nomini kiriting:",
        reply_markup=cancel_kb()
    )
    await state.set_state(ProductState.waiting_name)


@router.message(ProductState.waiting_name, admin_filter)
async def process_product_name(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=admin_products_kb())
        return

    await state.update_data(name=message.text.strip())
    await message.answer("📝 Mahsulot tavsifini kiriting (yoki '-'):")
    await state.set_state(ProductState.waiting_description)


@router.message(ProductState.waiting_description, admin_filter)
async def process_product_description(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=admin_products_kb())
        return

    description = "" if message.text.strip() == "-" else message.text.strip()
    await state.update_data(description=description)
    await message.answer("💰 Mahsulot narxini kiriting (so'mda):\nMasalan: 50000")
    await state.set_state(ProductState.waiting_price)


@router.message(ProductState.waiting_price, admin_filter)
async def process_product_price(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=admin_products_kb())
        return

    try:
        price = float(message.text.strip().replace(" ", "").replace(",", ""))
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Noto'g'ri narx. Faqat raqam kiriting:")
        return

    await state.update_data(price=price)
    await message.answer("📦 Ombordagi miqdorni kiriting (dona):")
    await state.set_state(ProductState.waiting_stock)


@router.message(ProductState.waiting_stock, admin_filter)
async def process_product_stock(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=admin_products_kb())
        return

    try:
        stock = int(message.text.strip())
        if stock < 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Noto'g'ri miqdor. Raqam kiriting:")
        return

    await state.update_data(stock=stock)
    await message.answer(
        "📏 Birlikni kiriting (yoki '-' bosing):\n"
        "Masalan: dona, kg, litr, juft..."
    )
    await state.set_state(ProductState.waiting_unit)


@router.message(ProductState.waiting_unit, admin_filter)
async def process_product_unit(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=admin_products_kb())
        return

    unit = "dona" if message.text.strip() == "-" else message.text.strip()
    await state.update_data(unit=unit)
    await message.answer("🖼 Mahsulot rasmini yuboring (yoki '-'):")
    await state.set_state(ProductState.waiting_photo)


@router.message(ProductState.waiting_photo, admin_filter)
async def process_product_photo(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=admin_products_kb())
        return

    photo = None
    if message.photo:
        photo = message.photo[-1].file_id
    elif message.text and message.text.strip() != "-":
        photo = message.text.strip()

    data = await state.get_data()
    product = await ProductModel.create(
        name=data["name"],
        price=data["price"],
        category_id=data["category_id"],
        description=data.get("description", ""),
        photo=photo,
        stock=data.get("stock", 0),
        unit=data.get("unit", "dona")
    )

    await state.clear()
    await message.answer(
        f"✅ Mahsulot qo'shildi!\n\n"
        f"📦 Nom: {product['name']}\n"
        f"💰 Narxi: {format_price(product['price'])}\n"
        f"📁 Kategoriya: {data.get('category_name', '')}\n"
        f"ID: {str(product['_id'])}",
        reply_markup=admin_products_kb(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("admin_del_prod_"))
async def delete_product(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q!", show_alert=True)
        return

    product_id = callback.data.replace("admin_del_prod_", "")
    deleted = await ProductModel.delete(product_id)

    if deleted:
        await callback.answer("✅ Mahsulot o'chirildi")
        await callback.message.delete()
    else:
        await callback.answer("❌ O'chirishda xato", show_alert=True)


@router.callback_query(F.data.startswith("admin_toggle_prod_"))
async def toggle_product(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q!", show_alert=True)
        return

    product_id = callback.data.replace("admin_toggle_prod_", "")
    product = await ProductModel.get_by_id(product_id)

    if not product:
        await callback.answer("Mahsulot topilmadi", show_alert=True)
        return

    new_status = not product.get("is_active", True)
    await ProductModel.update(product_id, is_active=new_status)

    status_text = "✅ Faollashtirildi" if new_status else "🚫 Faolsizlashtirildi"
    await callback.answer(status_text)
