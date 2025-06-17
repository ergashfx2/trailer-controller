from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

panel_key = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
    [KeyboardButton("➕ Add facility")],
    [KeyboardButton("🏢 All facilities")],
    [KeyboardButton("❌ Delete facility")]
])
