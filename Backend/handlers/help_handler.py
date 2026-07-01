from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def getHelpTextAndMarkup() -> tuple[str, InlineKeyboardMarkup]:
    message = "Рады представить вам Kefirchik - бота, который сделает деление общих трат в группах максимально простым и честным! 😎"
    markup = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Как пользоваться?", url=getInstructionLink())]]
    )
    return message, markup

def getInstructionLink() -> str:
    return "https://telegra.ph/Kefirchik---Gajd-po-samomu-chestnomu-deleniyu-trat-05-09"
