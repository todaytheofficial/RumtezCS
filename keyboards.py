from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def feedback_message_keyboard(group_msg_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Узнать отправителя",
                callback_data=f"whois:{group_msg_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                text="Замутить",
                callback_data=f"mute:{group_msg_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                text="Ответить от модератора",
                callback_data=f"reply:{group_msg_id}"
            ),
        ]
    ])


def cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отмена", callback_data="cancel")]
    ])