from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import ADMIN_IDS
from database import get_message_link, get_user_id_by_group_msg
from keyboards import cancel_keyboard

router = Router()


class ModeratorReply(StatesGroup):
    waiting_for_text = State()


class MuteUser(StatesGroup):
    waiting_for_duration = State()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


@router.callback_query(F.data.startswith("whois:"))
async def callback_whois(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав.", show_alert=True)
        return

    group_msg_id = int(callback.data.split(":")[1])
    data = get_message_link(group_msg_id)

    if data is None:
        await callback.answer("Информация об отправителе не найдена.", show_alert=True)
        return

    user_id = data["user_id"]
    username = data["user_username"]
    fullname = data["user_fullname"]

    text = (
        f"<b>Информация об отправителе:</b>\n\n"
        f"Имя: {fullname}\n"
        f"Username: {username}\n"
        f"ID: <code>{user_id}</code>\n"
        f"Ссылка: <a href='tg://user?id={user_id}'>открыть профиль</a>"
    )
    await callback.answer()
    await callback.message.reply(text, parse_mode="HTML")


@router.callback_query(F.data.startswith("mute:"))
async def callback_mute(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав.", show_alert=True)
        return

    group_msg_id = int(callback.data.split(":")[1])
    user_id = get_user_id_by_group_msg(group_msg_id)

    if user_id is None:
        await callback.answer("Пользователь не найден.", show_alert=True)
        return

    await state.set_state(MuteUser.waiting_for_duration)
    await state.update_data(target_user_id=user_id)

    await callback.answer()
    await callback.message.reply(
        f"Введите срок мута для пользователя <code>{user_id}</code>.\n\n"
        f"Форматы:\n"
        f"<code>30m</code> = 30 минут\n"
        f"<code>2h</code> = 2 часа\n"
        f"<code>1d</code> = 1 день\n"
        f"<code>7d</code> = 7 дней\n"
        f"<code>0</code> = снять мут",
        parse_mode="HTML",
        reply_markup=cancel_keyboard()
    )


@router.callback_query(F.data.startswith("reply:"))
async def callback_reply(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав.", show_alert=True)
        return

    group_msg_id = int(callback.data.split(":")[1])
    user_id = get_user_id_by_group_msg(group_msg_id)

    if user_id is None:
        await callback.answer("Пользователь не найден.", show_alert=True)
        return

    await state.set_state(ModeratorReply.waiting_for_text)
    await state.update_data(target_user_id=user_id)

    await callback.answer()
    await callback.message.reply(
        "Введите сообщение, которое будет отправлено пользователю от имени <b>Модератора</b>:",
        parse_mode="HTML",
        reply_markup=cancel_keyboard()
    )


@router.callback_query(F.data == "cancel")
async def callback_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer("Отменено", show_alert=False)
    await callback.message.edit_text("Действие отменено.")