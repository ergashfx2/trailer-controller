import asyncio
import datetime

from aiogram import types

from loader import dp,bot
from aiogram.types import ContentType

from utils.db_api.sqlite import db
import os
from PIL import Image
from aiogram.types import InputFile
from tempfile import mkdtemp
import shutil

chat_batches = {}
TIMEOUT = 5


def reset_batch(chat_id):
    if chat_id in chat_batches:
        task = chat_batches[chat_id].get("timeout_task")
        if task:
            task.cancel()
        del chat_batches[chat_id]


def resize_image(image, max_width=1024):
    if image.width > max_width:
        ratio = max_width / image.width
        new_height = int(image.height * ratio)
        return image.resize((max_width, new_height), Image.LANCZOS)
    return image


async def process_batch(chat_id):
    batch = chat_batches.get(chat_id)
    if not batch or batch.get("processing"):
        return  # already being processed or nothing to do

    batch["processing"] = True  # mark as in progress

    media_messages = batch.get("media", [])
    final_text = batch.get("final_text")
    if not final_text:
        batch["processing"] = False
        return

    final_text = final_text.split(" ")
    facility = db.get_facility_by_group(facility_group=str(chat_id))
    print(facility)
    main_text = (
        final_text[0] + " " + final_text[1] +
        "\n🚛 *Load* #" + final_text[3] +
        "\n\n📍 *Location:* " + facility[3] +
        "\n\nDate: " + str(datetime.date.today())
    )

    for msg in media_messages:
        try:
            await msg.forward(chat_id=facility[4])
        except Exception as e:
            print(f"Failed to forward media message: {e}")

    await bot.send_message(chat_id=facility[4], text=main_text, parse_mode=types.ParseMode.MARKDOWN)
    await bot.send_message(chat_id=facility[4], text="*Working on PDF....*", parse_mode=types.ParseMode.MARKDOWN)

    # Create PDF from photos
    temp_dir = mkdtemp()
    image_paths = []

    async def download_photo(bot, msg, path):
        photo = msg.photo[-1]
        await photo.download(destination_file=path)

    download_tasks = []
    for i, msg in enumerate(media_messages):
        if msg.content_type == ContentType.PHOTO:
            file_path = os.path.join(temp_dir, f"{i}.jpg")
            image_paths.append(file_path)
            download_tasks.append(download_photo(bot, msg, file_path))

    await asyncio.gather(*download_tasks)

    if image_paths:
        images = [resize_image(Image.open(p).convert("RGB")) for p in image_paths]
        pdf_path = os.path.join(temp_dir, "images.pdf")
        images[0].save(pdf_path, save_all=True, append_images=images[1:])
        try:
            await bot.send_document(chat_id=facility[4], document=InputFile(pdf_path))
        except Exception as e:
            print(f"Failed to send PDF: {e}")

        try:
            trailer_number = final_text[1].lower()
            trailer_status = final_text[0].lower()
            print(facility[0])
            db.add_trailer(trailer=trailer_number, status=trailer_status, facility=facility[0])
            print(f"✅ Trailer {trailer_number} added to DB.")
        except Exception as e:
            print(f"❌ Failed to add trailer: {e}")

    shutil.rmtree(temp_dir, ignore_errors=True)
    reset_batch(chat_id)





@dp.message_handler(content_types=ContentType.ANY)
async def handle_all(message: types.Message):
    chat_id = message.chat.id
    batch = chat_batches.setdefault(chat_id, {
        "media": [],
        "final_text": None,
        "timeout_task": None,
        "processing": False
    })
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



