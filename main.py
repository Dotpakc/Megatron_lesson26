import logging
import json

from decouple import config
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from utils import load_users, save_users

API_TOKEN = config('TG_API_KEY')

# Configure logging
logging.basicConfig(level=logging.INFO)


bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# проблема: після перезапуску бота, дані змінюються на ті, що вказані в users = [ ... ], тобто вони не зберігаються
users = load_users()

#States for FSM
class RegForm(StatesGroup):
    first_name = State()
    last_name = State()
    age = State()
    city = State()
    phone = State()

@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    if user_id not in [user['id'] for user in users]:
        await RegForm.first_name.set()
        await message.answer("Привіт, як тебе звати?")
        return
    
    await message.answer("Привіт, я бот)))")

@dp.message_handler(state=RegForm.first_name)
async def process_first_name(message: types.Message, state: FSMContext):
    await state.update_data(first_name=message.text)
    await RegForm.next()
    await message.answer("Яке твоє прізвище?")

@dp.message_handler(state=RegForm.last_name)
async def process_last_name(message: types.Message, state: FSMContext):
    await state.update_data(last_name=message.text)
    await RegForm.next()
    await message.answer("Який твій вік?")

@dp.message_handler(state=RegForm.age)
async def process_age(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Введи число")
        return
    
    await state.update_data(age=int(message.text))
    await RegForm.next()
    await message.answer("В якому місті ти живеш?")
    
@dp.message_handler(state=RegForm.city)
async def process_city(message: types.Message, state: FSMContext):
    await state.update_data(city=message.text.capitalize())
    await RegForm.next()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton(text="Відправити номер телефону", request_contact=True))
    await message.answer("Введи свій номер телефону", reply_markup=markup)

@dp.message_handler(state=RegForm.phone, content_types=types.ContentTypes.CONTACT)
async def process_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    data = await state.get_data()
    text = f"Перевірь дані:\nІм'я: {data['first_name']}\nПрізвище: {data['last_name']}\nВік: {data['age']}\nМісто: {data['city']}\nНомер телефону: {data['phone']}"
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton(text="Підтвердити"))
    markup.add(types.KeyboardButton(text="Спробувати ще раз"))
    await message.answer(text, reply_markup=markup)

@dp.message_handler(state=RegForm.phone, text="Спробувати ще раз")
async def process_phone_again(message: types.Message, state: FSMContext):
    await state.finish()
    await RegForm.first_name.set()
    await message.answer("Введи своє ім'я", reply_markup=types.ReplyKeyboardRemove())
    
@dp.message_handler(state=RegForm.phone, text="Підтвердити")
async def process_phone_confirm(message: types.Message, state: FSMContext):
    data = await state.get_data()
    users.append(dict(id=message.from_user.id, username=message.from_user.username, **data))
    save_users(users)
    await state.finish()
    await message.answer("Дякую, тепер ти зареєстрований", reply_markup=types.ReplyKeyboardRemove())
    await send_welcome(message)

@dp.message_handler()
async def echo(message: types.Message):
    await message.answer(message.text)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)