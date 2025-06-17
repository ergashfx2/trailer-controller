from aiogram.dispatcher.filters.state import StatesGroup, State


class PersonalData(StatesGroup):
    ID = State()
    answer = State()


class Texts(StatesGroup):
    caption = State()
    button = State()


class AddFacilityStates(StatesGroup):
    waiting_for_facility = State()
    waiting_for_facility_group = State()
    waiting_for_location = State()
    waiting_for_forwarding_group = State()

class DeleteFacilityStates(StatesGroup):
    waiting_for_id = State()