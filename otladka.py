import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
import wmi
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
from aiogram.types import ParseMode, InputFile
from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton
from afunc import vvod_dannyx_klienta, knopki_trenera
from pogoda import zapolnenie_bazy_pogody, pogoda_sytki
from sfunc import user_v_baze, fraza, informacia_o_trenirovke, redaktirovanie_trenirovki
from apscheduler.schedulers.asyncio import AsyncIOScheduler

f = open('token3.txt', 'r')
for line in f:
    API_TOKEN = line
f.close()

id_trenera = 1227721841

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

logging.basicConfig(level=logging.INFO)
log = logging.getLogger('broadcast')

scheduler = AsyncIOScheduler()
scheduler.add_job(zapolnenie_bazy_pogody, 'cron', hour=20, minute=21, misfire_grace_time=300)
scheduler.start()

@dp.message_handler(commands=['start'])
async def echo(message: types.Message):
    class Form_na(StatesGroup):
        Novyi_adres = State()

    await Form_na.Novyi_adres.set()
    await bot.send_message(id_trenera, "Введите новый адрес.")

    @dp.message_handler(state=Form_na.Novyi_adres)
    async def process_name1(message: types.Message, state: FSMContext):
        print('Новый адрес:', message.text)
        znachenie = message.text
        redaktirovanie_trenirovki(77, 'adres', znachenie)




executor.start_polling(dp, skip_updates=True)