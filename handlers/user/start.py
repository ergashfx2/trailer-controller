from aiogram import types
from filters.admins import AdminFilter
from loader import bot, dp
from utils.db_api.sqlite import db
from loader import dp
from aiogram.dispatcher.filters import Command, Text
from aiogram.types import Message, ReplyKeyboardRemove


@dp.message_handler(commands="start")
async def send(message: Message):
    await message.answer("*Salom*",
                         parse_mode="markdown")

