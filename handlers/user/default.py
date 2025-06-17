import asyncio
import datetime

from aiogram import types

from loader import dp,bot
from aiogram.types import ContentType

from utils.db_api.sqlite import db

chat_batches = {}
TIMEOUT = 5


def reset_batch(chat_id):
    if chat_id in chat_batches:
        task = chat_batches[chat_id].get("timeout_task")
        if task:
            task.cancel()
        del chat_batches[chat_id]


async def process_batch(chat_id):
    batch = chat_batches.get(chat_id)
    if not batch:
        return

    media_messages = batch.get("media", [])
    final_text = batch.get("final_text").split(" ")
    facility = db.get_facility_by_group(facility_group=str(chat_id))
    main_text = final_text[0] + " " + final_text[1] + "\n🚛 *Load* #" + final_text[4]  + "\n\n" + "📍 *Location:*  " + facility[3] + "\n\nDate :" + str(datetime.date.today())

    for msg in media_messages:
        try:
            await msg.forward(chat_id=facility[4])
        except Exception as e:
            print(f"Failed to forward media message: {e}")
    await bot.send_message(chat_id=facility[4], text=main_text,parse_mode=types.ParseMode.MARKDOWN)
    reset_batch(chat_id)


@dp.message_handler(content_types=ContentType.ANY)
async def handle_all(message: types.Message):
    chat_id = message.chat.id
    batch = chat_batches.setdefault(chat_id, {"media": [], "final_text": None, "timeout_task": None})
    if (message.content_type in [ContentType.PHOTO, ContentType.VIDEO]) and message.media_group_id is None:
        batch["media"].append(message)
        if batch["timeout_task"]:
            batch["timeout_task"].cancel()
        batch["timeout_task"] = asyncio.create_task(timeout_handler(chat_id))
    elif message.media_group_id:
        if message.content_type in [ContentType.PHOTO, ContentType.VIDEO]:
            batch["media"].append(message)
            if batch["timeout_task"]:
                batch["timeout_task"].cancel()
            batch["timeout_task"] = asyncio.create_task(timeout_handler(chat_id))
    elif message.forward_from or message.forward_from_chat:
        if batch and not batch.get("final_text"):
            batch["final_text"] = message.text or message.caption
            await process_batch(chat_id)



async def timeout_handler(chat_id):
    await asyncio.sleep(TIMEOUT)
    await process_batch(chat_id)



