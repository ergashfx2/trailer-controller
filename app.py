from aiogram import executor
from loader import dp
import middlewares, filters, handlers
import logging
logging.basicConfig(level=logging.INFO)

if __name__ == '__main__':
    executor.start_polling(dp)
