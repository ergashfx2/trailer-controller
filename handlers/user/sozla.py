from aiogram import types
from aiogram.dispatcher import FSMContext
from filters.admins import AdminFilter
from loader import bot, dp
from keyboards.inline.admin import admin_main, admin_second, cancel, create_channels_button, create_admins_button, \
    yes_no
from aiogram.types import CallbackQuery
from utils.db_api.sqlite import db
from data.states import PersonalData, Texts, AddFacilityStates, DeleteFacilityStates
from data.config import CHANNELS, ADMINS, Text_caption, Button_text
from keyboards.default.panel import panel_key


@dp.message_handler(commands="cancel", state="*")
async def cancel_handler(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("❌ Operation canceled.", reply_markup=panel_key)


@dp.message_handler(AdminFilter(), text="/admin")
async def welcome(msg: types.Message, state: FSMContext):
    await msg.answer("*Xush kelibsiz admin*", parse_mode="markdown", reply_markup=admin_main)


@dp.callback_query_handler(AdminFilter(), text="main")
async def add_channel(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer("*Xush kelibsiz admin*", parse_mode="markdown", reply_markup=admin_main)


@dp.callback_query_handler(AdminFilter(), text="main",
                           state=["remove_channel", "add_channel", PersonalData.ID, PersonalData.answer])
async def add_channel(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer("*Xush kelibsiz admin*", parse_mode="markdown", reply_markup=admin_main)
    await state.finish()


@dp.callback_query_handler(AdminFilter(), text="add")
async def add_channel(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer("Kanaldan postni forward qiling", reply_markup=cancel)
    await state.set_state("add_channel")


@dp.callback_query_handler(AdminFilter(), text="add_text")
async def add_channel(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer("*Matn kiriting*", parse_mode="markdown", reply_markup=cancel)
    await Texts.caption.set()


@dp.message_handler(AdminFilter(), state=Texts.caption)
async def add_channel(call: types.Message, state: FSMContext):
    await state.update_data({"caption": call.text})
    await call.answer("Tugma uchun matn kiriting", reply_markup=cancel)
    await Texts.next()


@dp.message_handler(AdminFilter(), state=Texts.button)
async def add_channel(call: types.Message, state: FSMContext):
    await state.update_data({"button": call.text})
    data = await state.get_data()
    matn = data.get("caption")
    button = data.get("button")
    db.delete_texts()
    await call.answer("*✅ Saqlandi*", parse_mode="markdown")
    Text_caption.clear()
    Button_text.clear()
    Text_caption.append(matn)
    Button_text.append(button)
    db.add_text(caption=matn, button=button)
    await state.finish()


@dp.callback_query_handler(AdminFilter(), text="remove")
async def add_channel(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    channels = db.select_all_channels()
    print(channels)
    list = {}
    for channel in channels:
        list[channel[2]] = f"{channel[1]}"
    kanallar = create_channels_button(names=list)
    await call.message.answer("Kanalni tanlang", reply_markup=kanallar)
    print(list)
    await state.set_state("remove_channel")


@dp.callback_query_handler(AdminFilter(), text="channels")
async def add_channel(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    channels = db.select_all_channels()
    list = {}
    for channel in channels:
        list[channel[2]] = f"{channel[1]}"
    kanallar = create_channels_button(names=list)
    await call.message.answer("*Kanallar ro'yxati*", parse_mode="markdown", reply_markup=kanallar)


@dp.callback_query_handler(AdminFilter(), text="admins")
async def add_channel(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    admins = db.select_all_admins()
    list = {}
    for admin in admins:
        list[admin[2]] = f"{admin[1]}"
    laminar = create_admins_button(names=list)
    await call.message.answer("*Adminlar ro'yxati*", parse_mode="markdown", reply_markup=laminar)
    await PersonalData.ID.set()


@dp.callback_query_handler(AdminFilter(), text="add_text")
async def add_channel(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer("Matn kiriting", reply_markup=cancel)
    await state.set_state("add_text")


@dp.callback_query_handler(AdminFilter(), text="add_admin", state=PersonalData.ID)
async def add_channel(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer("*Qo'shmoqchi bo'lgan odamdan xabarni forward qiling*", parse_mode="markdown",
                              reply_markup=cancel)
    await state.finish()
    await state.set_state("add_admin")


@dp.callback_query_handler(AdminFilter(), text="button")
async def add_channel(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer("Matn kiriting", reply_markup=cancel)
    await state.set_state("button")


@dp.callback_query_handler(AdminFilter(), text="settings")
async def add_channel(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer("*Qo'shimcha bo'lim*", parse_mode="Markdown", reply_markup=admin_second)


@dp.callback_query_handler(AdminFilter(), text="cancel")
async def add_channel(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer("❌ Amal bekor qilindi", reply_markup=admin_main)


@dp.callback_query_handler(AdminFilter(), text="hide")
async def add_channel(call: CallbackQuery, state: FSMContext):
    await call.message.delete()


# States

@dp.message_handler(AdminFilter(), content_types=types.ContentType.ANY, state="add_channel")
async def add_base(msg: types.Message, state: FSMContext):
    channel_id = msg.forward_from_chat.id
    try:
        try:
            chat_member = await bot.get_chat_member(channel_id, bot.id)
            if chat_member.is_chat_admin():
                channel = await bot.get_chat(int(channel_id))
                print(channel)
                channel_name = channel.full_name
                channel_users = await bot.get_chat_members_count(chat_id=channel_id)
                print(channel_users)
                db.add_channel(channel_id=channel_id, channel_name=channel_name, channel_users=channel_users)
                await msg.answer("✅ *Kanal ulandi*", parse_mode="markdown")
                await state.finish()
                await msg.answer("*Xush kelibsiz admin*", parse_mode="markdown", reply_markup=admin_main)
                CHANNELS.append(channel_id)
            else:
                await msg.answer("❌ *Bot kanalda admin emas*", parse_mode="markdown")
                await msg.answer("*Xush kelibsiz admin*", parse_mode="markdown", reply_markup=admin_main)
                await state.finish()
        except:
            await msg.answer("❌ *Bot kanalda admin emas*", parse_mode="markdown")
            await msg.answer("*Xush kelibsiz admin*", parse_mode="markdown", reply_markup=admin_main)
            await state.finish()
    except:
        await msg.answer("❌ *Bot kanalda admin emas*", parse_mode="markdown")
        await msg.answer("*Xush kelibsiz admin*", parse_mode="markdown", reply_markup=admin_main)
        await state.finish()


@dp.callback_query_handler(AdminFilter(), state="remove_channel")
async def remove_channel(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    channel_name = call.data
    db.delete_channel(channel=channel_name)
    await call.message.answer(f"*{channel_name}* - ID li kanal botdan uzib qo'yildi", parse_mode="markdown")
    CHANNELS.remove(int(channel_name))
    await call.message.answer("*Xush kelibsiz admin*", parse_mode="markdown", reply_markup=admin_main)
    await state.finish()


@dp.message_handler(AdminFilter(), content_types=types.ContentType.ANY, state="add_admin")
async def add_admin(msg: types.Message, state: FSMContext):
    try:
        id = msg.forward_from.id
        name = msg.forward_from.full_name
        db.add_admin(cid=id, name=name)
        await msg.answer(f"{name} - Ismli admin qo'shildi")
        ADMINS.append(id)
        await msg.answer("*Xush kelibsiz admin*", parse_mode="markdown", reply_markup=admin_main)
        await state.finish()
    except:
        await msg.answer("Siz forward qilmadingiz", reply_markup=admin_main)
        await state.finish()


@dp.callback_query_handler(state=PersonalData.ID)
async def delete_admin(call: types.CallbackQuery, state: FSMContext):
    await state.update_data({"ID": call.data})
    await call.message.delete()
    await call.message.answer(
        f"*Siz haqiqatdan ham ushbu adminni o'chirib tashlaysizmi ?*\n\n*ID :* {call.data}",
        parse_mode="markdown", reply_markup=yes_no)
    await PersonalData.next()


@dp.callback_query_handler(state=PersonalData.answer)
async def delete_admin(call: types.CallbackQuery, state: FSMContext):
    answer = call.data
    data = await state.get_data()
    id = data.get("ID")
    if answer == "yes":
        db.delete_admin(cid=id)
        ADMINS.remove(int(id))
        await call.message.answer(f"*{id}* - ID ga ega admin olib tashlandi", parse_mode="markdown")
        await state.finish()
        await call.message.delete()
        await call.message.answer("*Xush kelibsiz admin*", parse_mode="markdown", reply_markup=admin_main)
    else:
        admins = db.select_all_admins()
        list = {}
        for admin in admins:
            list[admin[2]] = f"{admin[1]}"
        await call.message.answer("Siz amalni bekor qildingiz", reply_markup=create_admins_button(list))
        await state.finish()
        await call.message.delete()
        await call.message.answer("*Xush kelibsiz admin*", parse_mode="markdown", reply_markup=admin_main)



@dp.message_handler(AdminFilter(),text="/panel")
async def panel(msg: types.Message, state: FSMContext):
    await msg.answer("*Please choose correct options* ", parse_mode="markdown",reply_markup=panel_key)


@dp.message_handler(AdminFilter(),lambda message: message.text == "➕ Add facility")
async def start_add_facility(message: types.Message):
    await message.answer("🏢 Enter facility name:")
    await AddFacilityStates.waiting_for_facility.set()

@dp.message_handler(AdminFilter(),state=AddFacilityStates.waiting_for_facility)
async def get_facility(message: types.Message, state: FSMContext):
    await state.update_data(facility=message.text)
    await message.answer("👥 Enter facility group name:")
    await AddFacilityStates.waiting_for_facility_group.set()


@dp.message_handler(AdminFilter(),state=AddFacilityStates.waiting_for_facility_group)
async def get_facility_group(message: types.Message, state: FSMContext):
    await state.update_data(facility_group=message.text)
    await message.answer("📍 Enter facility location:")
    await AddFacilityStates.waiting_for_location.set()


@dp.message_handler(AdminFilter(),state=AddFacilityStates.waiting_for_location)
async def get_location(message: types.Message, state: FSMContext):
    await state.update_data(facility_location=message.text)
    await message.answer("📤 Enter forwarding group ID (e.g. -1001234567890):")
    await AddFacilityStates.waiting_for_forwarding_group.set()


@dp.message_handler(AdminFilter(),state=AddFacilityStates.waiting_for_forwarding_group)
async def get_forwarding_group(message: types.Message, state: FSMContext):
    await state.update_data(forwarding_group=message.text)
    data = await state.get_data()

    # Add to database
    db.add_facility(
        data['facility'],
        data['facility_group'],
        data['facility_location'],
        data['forwarding_group']
    )

    await message.answer("✅ Facility added successfully!", reply_markup=panel_key)
    await state.finish()

@dp.message_handler(lambda msg: msg.text == "🏢 All facilities")
async def show_facilities(message: types.Message):
    facilities = db.get_facility()
    if not facilities:
        await message.answer("⚠️ No facilities found.")
        return

    response = "🏢 *Facilities List:*\n\n"
    for f in facilities:
        response += f"🆔 ID: `{f[0]}`\n🏭 Name: *{f[1]}*\n👥 Group: `{f[2]}`\n📍 Location: _{f[3]}_\n🔁 Forward To: `{f[4]}`\n\n"

    await message.answer(response, parse_mode="Markdown")


@dp.message_handler(lambda msg: msg.text == "❌ Delete facility")
async def ask_delete_facility(message: types.Message):
    await message.answer("🆔 Enter facility ID to delete (or /cancel):")
    await DeleteFacilityStates.waiting_for_id.set()

@dp.message_handler(state=DeleteFacilityStates.waiting_for_id)
async def delete_facility_handler(message: types.Message, state: FSMContext):
    try:
        f_id = int(message.text.strip())
        deleted = db.delete_facility(f_id)
        await message.answer(f"✅ Facility with ID `{f_id}` has been deleted.", parse_mode="Markdown")
    except Exception:
        await message.answer("❌ Invalid ID or database error.")
    await state.finish()
