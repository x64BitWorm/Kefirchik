from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def getHelpTextAndMarkup() -> tuple[str, InlineKeyboardMarkup]:
    message = "Рады представить вам Kefirchik - бота, который сделает деление общих трат в группах максимально простым и честным! 😎"
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("Как пользоваться?", url=getInstructionLink())]
    ])
    return message, markup

def getInstructionLink() -> str:
    return "https://telegra.ph/Kefirchik---Gajd-po-samomu-chestnomu-deleniyu-trat-05-09"
