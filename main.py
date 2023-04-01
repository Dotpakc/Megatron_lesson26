import logging

from decouple import config
from aiogram import Bot, Dispatcher, executor, types


API_TOKEN = config('TG_API_KEY')

# Configure logging
logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await message.answer("Привіт, я бот)))")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)