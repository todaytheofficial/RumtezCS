from aiogram import Router, Bot, F
from aiogram.types import Message
from aiogram.filters import CommandStart
import time

from config import GROUP_CHAT_ID
from database import save_message_link, is_muted
from keyboards import feedback_message_keyboard

router = Router()


def format_remaining_time(muted_until: float) -> str:
    remaining = int(muted_until - time.time())
    if remaining <= 0:
        return "менее минуты"
    hours, remainder = divmod(remaining, 3600)
    minutes, seconds = divmod(remainder, 60)
    parts = []
    if hours > 0:
        parts.append(f"{hours}ч")
    if minutes > 0:
        parts.append(f"{minutes}мин")
    if seconds > 0 and hours == 0:
        parts.append(f"{seconds}с")
    return " ".join(parts)


@router.message(CommandStart())
async def cmd_start(message: Message):
    muted, muted_until = is_muted(message.from_user.id)
    if muted:
        remaining = format_remaining_time(muted_until)
        await message.answer(
            f"Вы замучены. Доступ к боту будет восстановлен через {remaining}."
        )
        return

    await message.answer(
        "Привет! Напишите сюда любое сообщение, оно будет анонимно передано модераторам.\n\n"
        "Поддерживаются: текст, фото, видео, документы, голосовые, стикеры."
    )


@router.message(F.chat.type == "private")
async def handle_user_message(message: Message, bot: Bot):
    muted, muted_until = is_muted(message.from_user.id)
    if muted:
        remaining = format_remaining_time(muted_until)
        await message.answer(f"Вы замучены. Попробуйте через {remaining}.")
        return

    user = message.from_user
    username = f"@{user.username}" if user.username else "нет"
    fullname = user.full_name or "Неизвестный"

    header = "<b>Новое анонимное сообщение</b>"

    try:
        sent = None

        if message.text:
            sent = await bot.send_message(
                chat_id=GROUP_CHAT_ID,
                text=f"{header}\n\n{message.text}",
                parse_mode="HTML"
            )
        elif message.photo:
            sent = await bot.send_photo(
                chat_id=GROUP_CHAT_ID,
                photo=message.photo[-1].file_id,
                caption=f"{header}\n\n{message.caption or ''}",
                parse_mode="HTML"
            )
        elif message.video:
            sent = await bot.send_video(
                chat_id=GROUP_CHAT_ID,
                video=message.video.file_id,
                caption=f"{header}\n\n{message.caption or ''}",
                parse_mode="HTML"
            )
        elif message.document:
            sent = await bot.send_document(
                chat_id=GROUP_CHAT_ID,
                document=message.document.file_id,
                caption=f"{header}\n\n{message.caption or ''}",
                parse_mode="HTML"
            )
        elif message.voice:
            sent = await bot.send_voice(
                chat_id=GROUP_CHAT_ID,
                voice=message.voice.file_id,
                caption=header,
                parse_mode="HTML"
            )
        elif message.audio:
            sent = await bot.send_audio(
                chat_id=GROUP_CHAT_ID,
                audio=message.audio.file_id,
                caption=f"{header}\n\n{message.caption or ''}",
                parse_mode="HTML"
            )
        elif message.sticker:
            header_msg = await bot.send_message(
                chat_id=GROUP_CHAT_ID,
                text=header,
                parse_mode="HTML"
            )
            sent = await bot.send_sticker(
                chat_id=GROUP_CHAT_ID,
                sticker=message.sticker.file_id
            )
            save_message_link(header_msg.message_id, user.id, username, fullname)
        elif message.video_note:
            sent = await bot.send_video_note(
                chat_id=GROUP_CHAT_ID,
                video_note=message.video_note.file_id
            )
        else:
            await message.answer("Этот тип сообщения не поддерживается.")
            return

        if sent:
            try:
                await sent.edit_reply_markup(
                    reply_markup=feedback_message_keyboard(sent.message_id)
                )
            except Exception:
                ctrl_msg = await bot.send_message(
                    chat_id=GROUP_CHAT_ID,
                    text="Управление сообщением выше:",
                    reply_markup=feedback_message_keyboard(sent.message_id)
                )
                save_message_link(ctrl_msg.message_id, user.id, username, fullname)

            save_message_link(sent.message_id, user.id, username, fullname)

        await message.answer("Ваше сообщение отправлено модераторам!")

    except Exception as e:
        await message.answer("Произошла ошибка при отправке. Попробуйте позже.")
        print(f"Error forwarding message: {e}")