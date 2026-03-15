from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from app.keyboards import admin_categories_kb
from app.keyboards.admin_kb import cancel_kb, category_manage_kb
from app.models import CategoryModel
from app.utils import is_admin

router = Router()


def admin_filter(message: Message) -> bool:
    return is_admin(message.from_user.id)


class CategoryState(StatesGroup):
    waiting_name = State()
    waiting_description = State()
    waiting_photo = State()


@router.message(F.text == "📁 Kategoriyalar", admin_filter)
async def categories_menu(message: Message):
    await message.answer(
        "📁 Kategoriyalar boshqaruvi:",
        reply_markup=admin_categories_kb()
    )


@router.message(F.text == "📋 Kategoriyalar ro'yxati", admin_filter)
async def categories_list(message: Message):
    categories = await CategoryModel.get_all()

    if not categories:
        await message.answer("😕 Kategoriyalar yo'q.")
        return

    for cat in categories:
        status = "✅" if cat.get("is_active") else "🚫"
        text = f"{status} <b>{cat['name']}</b>\nID: {str(cat['_id'])}"
        await message.answer(
            text,
            reply_markup=category_manage_kb(str(cat["_id"])),
            parse_mode="HTML"
        )


@router.message(F.text == "➕ Kategoriya qo'shish", admin_filter)
async def add_category_start(message: Message, state: FSMContext):
    await message.answer(
        "📁 Yangi kategoriya nomini kiriting:",
        reply_markup=cancel_kb()
    )
    await state.set_state(CategoryState.waiting_name)


@router.message(CategoryState.waiting_name, admin_filter)
async def process_category_name(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=admin_categories_kb())
        return

    await state.update_data(name=message.text.strip())
    await message.answer(
        "📝 Kategoriya tavsifini kiriting (yoki o'tkazib yuborish uchun '-' kiriting):"
    )
    await state.set_state(CategoryState.waiting_description)


@router.message(CategoryState.waiting_description, admin_filter)
async def process_category_description(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=admin_categories_kb())
        return

    description = "" if message.text.strip() == "-" else message.text.strip()
    await state.update_data(description=description)

    await message.answer(
        "🖼 Kategoriya rasmini yuboring (yoki '-' kiriting):"
    )
    await state.set_state(CategoryState.waiting_photo)


@router.message(CategoryState.waiting_photo, admin_filter)
async def process_category_photo(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=admin_categories_kb())
        return

    photo = None
    if message.photo:
        photo = message.photo[-1].file_id
    elif message.text and message.text.strip() != "-":
        photo = message.text.strip()

    data = await state.get_data()
    category = await CategoryModel.create(
        name=data["name"],
        description=data.get("description", ""),
        photo=photo
    )

    await state.clear()
    await message.answer(
        f"✅ Kategoriya qo'shildi!\n\n"
        f"📁 Nom: {category['name']}\n"
        f"ID: {str(category['_id'])}",
        reply_markup=admin_categories_kb(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("admin_del_cat_"))
async def delete_category(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q!", show_alert=True)
        return

    category_id = callback.data.replace("admin_del_cat_", "")
    deleted = await CategoryModel.delete(category_id)

    if deleted:
        await callback.answer("✅ Kategoriya o'chirildi")
        await callback.message.delete()
    else:
        await callback.answer("❌ O'chirishda xato", show_alert=True)
