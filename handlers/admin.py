from aiogram import Router, Bot, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from config import ADMIN_IDS, GROUP_CHAT_ID
from database import mute_user, unmute_user, get_user_id_by_group_msg, save_message_link
from handlers.callbacks import ModeratorReply, MuteUser

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def parse_duration(text: str) -> int | None:
    text = text.strip().lower()

    if text == "0":
        return 0

    multipliers = {
        "m": 60,
        "h": 3600,
        "d": 86400,
    }

    if len(text) < 2:
        return None

    unit = text[-1]
    if unit not in multipliers:
        return None

    try:
        amount = int(text[:-1])
    except ValueError:
        return None

    if amount <= 0:
        return None

    return amount * multipliers[unit]


def format_duration(seconds: int) -> str:
    if seconds < 3600:
        return f"{seconds // 60} мин."
    elif seconds < 86400:
        return f"{seconds // 3600} ч."
    else:
        return f"{seconds // 86400} дн."


@router.message(MuteUser.waiting_for_duration, F.chat.type.in_({"private", "group", "supergroup"}))
async def process_mute_duration(message: Message, state: FSMContext, bot: Bot):
    if not is_admin(message.from_user.id):
        return

    data = await state.get_data()
    target_user_id = data.get("target_user_id")

    if target_user_id is None:
        await state.clear()
        await message.reply("Ошибка: пользователь не найден.")
        return

    text = message.text.strip()

    if text == "0":
        unmute_user(target_user_id)
        await state.clear()
        await message.reply(
            f"Мут снят с пользователя <code>{target_user_id}</code>.",
            parse_mode="HTML"
        )
        try:
            await bot.send_message(
                target_user_id,
                "Ваш мут снят. Вы снова можете отправлять сообщения."
            )
        except:
            pass
        return

    duration = parse_duration(text)
    if duration is None:
        await message.reply(
            "Неверный формат. Используйте:\n"
            "<code>30m</code>, <code>2h</code>, <code>1d</code>, <code>0</code> (снять мут)",
            parse_mode="HTML"
        )
        return

    mute_user(target_user_id, duration)
    await state.clear()

    formatted = format_duration(duration)
    await message.reply(
        f"Пользователь <code>{target_user_id}</code> замучен на {formatted}.",
        parse_mode="HTML"
    )

    try:
        await bot.send_message(
            target_user_id,
            f"Вы были замучены модератором на {formatted}.\n"
            f"В течение этого времени вы не сможете отправлять сообщения."
        )
    except:
        pass


@router.message(ModeratorReply.waiting_for_text, F.chat.type.in_({"private", "group", "supergroup"}))
async def process_moderator_reply(message: Message, state: FSMContext, bot: Bot):
    if not is_admin(message.from_user.id):
        return

    data = await state.get_data()
    target_user_id = data.get("target_user_id")

    if target_user_id is None:
        await state.clear()
        await message.reply("Ошибка: пользователь не найден.")
        return

    await state.clear()

    try:
        await bot.send_message(
            target_user_id,
            f"<b>Сообщение от Модератора:</b>\n\n{message.text}",
            parse_mode="HTML"
        )
        await message.reply("Сообщение отправлено пользователю.")
    except Exception as e:
        await message.reply(f"Не удалось отправить сообщение: {e}")


@router.message(F.chat.id == GROUP_CHAT_ID, F.reply_to_message)
async def handle_group_reply(message: Message, bot: Bot, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    current_state = await state.get_state()
    if current_state is not None:
        return

    replied_msg_id = message.reply_to_message.message_id
    user_id = get_user_id_by_group_msg(replied_msg_id)

    if user_id is None:
        return

    if not message.text:
        return

    try:
        await bot.send_message(
            user_id,
            f"<b>Сообщение от Модератора:</b>\n\n{message.text}",
            parse_mode="HTML"
        )
        await message.reply("Сообщение доставлено пользователю.")
    except Exception as e:
        await message.reply(f"Не удалось отправить: {e}")