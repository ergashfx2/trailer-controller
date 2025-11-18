

from aiogram.dispatcher.filters import BoundFilter
from aiogram import types

class IsGroup(BoundFilter):
    async def check(self, message: types.Message):
        return message.chat.type in [types.ChatType.GROUP, types.ChatType.SUPERGROUP]

class IsPDFGroup(BoundFilter):
    async def check_group(self,types.Message):
        return message.chat.id in [-1003341826791,"-1003341826791"]
