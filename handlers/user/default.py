import asyncio
import datetime
import uuid

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

chat_buffers = {
    'chat_id': {
        "photos": [],           # photo Message objectlarini saqlaymiz
        "last_msg": None,       # PDFni oxirgi xabarga reply qilish uchun
        "timer": None           # debounce timeout task
    }
}

async def debounce(chat_id, wait=2):
    await asyncio.sleep(wait)
    buffer = chat_buffers.get(chat_id)
    if buffer and buffer["photos"]:
        await make_pdf(chat_id)


async def make_pdf(chat_id):
    buffer = chat_buffers.get(chat_id)
    if not buffer: return
    await bot.send_message(chat_id=chat_id, text="*Converting in progress.......*",parse_mode="Markdown")
    temp_paths = []
    for msg in buffer["photos"]:
        file = await bot.get_file(msg.photo[-1].file_id)
        path = f"temp_{msg.message_id}.jpg"
        await bot.download_file(file.file_path, path)
        temp_paths.append(path)

    # PDF yaratish
    from PIL import Image
    images = [Image.open(p).convert("RGB") for p in temp_paths]
    file_name = uuid.uuid4()
    pdf_path = f"{file_name}.pdf"
    images[0].save(pdf_path, save_all=True, append_images=images[1:])
    await buffer["last_msg"].reply_document(open(pdf_path, "rb"))

    if os.path.exists(f"{file_name}.pdf"):
        os.remove(f"temp_{file_name}.pdf")
        print("File deleted successfully")
    else:
        print("File not found")

    for p in temp_paths:
        os.remove(p)
    buffer["photos"].clear()
    buffer["last_msg"] = None
    buffer["timer"] = None


@dp.message_handler(content_types=[ContentType.PHOTO])
async def handle_photo(message: types.Message):
    if (message.chat.id == -1003341826791):
        chat_id = message.chat.id
        buffer = chat_buffers.setdefault(chat_id, {"photos": [], "last_msg": None, "timer": None})
        buffer["photos"].append(message)
        buffer["last_msg"] = message
        if buffer["timer"]:
            buffer["timer"].cancel()
        buffer["timer"] = asyncio.create_task(debounce(chat_id))
    else:
        pass



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



