from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from app.keyboards import admin_main_kb
from app.keyboards.admin_kb import cancel_kb
from app.keyboards.user_kb import confirm_kb
from app.models import UserModel
from app.utils import is_admin
import asyncio

router = Router()


def admin_filter(message: Message) -> bool:
    return is_admin(message.from_user.id)


class BroadcastState(StatesGroup):
    waiting_message = State()
    waiting_confirm = State()


@router.message(F.text == "📢 Xabar yuborish", admin_filter)
async def broadcast_start(message: Message, state: FSMContext):
    await message.answer(
        "📢 Barcha foydalanuvchilarga yuboriladigan xabarni kiriting:\n\n"
        "<i>Matn, rasm, video yoki hujjat yuborishingiz mumkin.</i>",
        reply_markup=cancel_kb(),
        parse_mode="HTML"
    )
    await state.set_state(BroadcastState.waiting_message)


@router.message(BroadcastState.waiting_message, admin_filter)
async def process_broadcast_message(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=admin_main_kb())
        return

    # Xabar ma'lumotlarini saqlash
    msg_data = {
        "text": message.text,
        "photo": message.photo[-1].file_id if message.photo else None,
        "video": message.video.file_id if message.video else None,
        "caption": message.caption,
        "message_id": message.message_id,
        "chat_id": message.chat.id,
    }
    await state.update_data(msg_data=msg_data)

    user_count = await UserModel.count()
    await message.answer(
        f"📢 Xabar {user_count} ta foydalanuvchiga yuboriladi.\n\n"
        f"Tasdiqlaysizmi?",
        reply_markup=confirm_kb("broadcast_yes", "broadcast_no")
    )
    await state.set_state(BroadcastState.waiting_confirm)


@router.message(F.text, BroadcastState.waiting_confirm, admin_filter)
async def handle_broadcast_text(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=admin_main_kb())


from aiogram.types import CallbackQuery


@router.callback_query(F.data == "broadcast_no", BroadcastState.waiting_confirm)
async def broadcast_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Xabar yuborish bekor qilindi.")
    await callback.message.answer(
        "Admin menyu:", reply_markup=admin_main_kb()
    )


@router.callback_query(F.data == "broadcast_yes", BroadcastState.waiting_confirm)
async def broadcast_send(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    msg_data = data.get("msg_data", {})

    users = await UserModel.get_all(limit=10000)
    await state.clear()

    await callback.message.edit_text(
        f"📤 Xabar {len(users)} ta foydalanuvchiga yuborilmoqda..."
    )

    success = 0
    failed = 0

    for user in users:
        try:
            if msg_data.get("photo"):
                await callback.bot.send_photo(
                    chat_id=user["telegram_id"],
                    photo=msg_data["photo"],
                    caption=msg_data.get("caption", "")
                )
            elif msg_data.get("video"):
                await callback.bot.send_video(
                    chat_id=user["telegram_id"],
                    video=msg_data["video"],
                    caption=msg_data.get("caption", "")
                )
            elif msg_data.get("text"):
                await callback.bot.send_message(
                    chat_id=user["telegram_id"],
                    text=msg_data["text"],
                    parse_mode="HTML"
                )
            success += 1
            await asyncio.sleep(0.05)  # Flood limitni oldini olish
        except Exception:
            failed += 1

    await callback.message.answer(
        f"✅ Xabar yuborildi!\n\n"
        f"✅ Muvaffaqiyatli: {success}\n"
        f"❌ Xato: {failed}",
        reply_markup=admin_main_kb()
    )
