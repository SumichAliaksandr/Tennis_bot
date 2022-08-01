import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
import wmi
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
from aiogram.types import ParseMode, InputFile
from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton
from afunc import vvod_dannyx_klienta, knopki_trenera, knopki_klienta, otmena_trenirovok_esli_malo_zapisalos, \
    napominanie_o_trenirovke_za_1_chas, zamena_knopok, naznachit_trenirovky, chistki_info
from pogoda import pogoda_na_6_dney
from sfunc import user_v_baze, fraza
from apscheduler.schedulers.asyncio import AsyncIOScheduler

f = open('token3.txt', 'r')
for line in f:
    API_TOKEN = line
f.close()

id_trenera = 1227721841
#id_trenera = 1227721842

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

logging.basicConfig(level=logging.INFO)
log = logging.getLogger('broadcast')

scheduler = AsyncIOScheduler()
for i in range(7,22):
    scheduler.add_job(otmena_trenirovok_esli_malo_zapisalos, 'cron', hour=i, minute=0, args=(dp,), misfire_grace_time=300)
    scheduler.add_job(napominanie_o_trenirovke_za_1_chas, 'cron', hour=i, minute=1, args=(dp,), misfire_grace_time=300)

for i in range(7,22):
    scheduler.add_job(zamena_knopok, 'cron', hour=i, minute=1, args=(dp,), misfire_grace_time=300)


scheduler.add_job(pogoda_na_6_dney, 'cron', hour=20, minute=20, misfire_grace_time=300)
scheduler.add_job(pogoda_na_6_dney, 'cron', hour=21, minute=30, misfire_grace_time=300)


scheduler.add_job(chistki_info, 'cron', hour=0, minute=2, args=(dp,), misfire_grace_time=300)
scheduler.start()

@dp.message_handler(commands=['start'], state='*')
async def echo(message: types.Message, state: FSMContext):
    await state.finish()

    user = message.from_user.id
    if user == id_trenera:
        #await knopki_trenera(id_trenera, dp)
        now = datetime.now()
        data = now.strftime("%d.%m")
        await naznachit_trenirovky(id_trenera, '0', data, dp)
    else:

        if user_v_baze(user):
            print('v baze')
            now = datetime.now()
            data_zapisi = now.strftime("%d.%m")
            await knopki_klienta(user, '0', data_zapisi, dp)

        else:
            await vvod_dannyx_klienta(user, dp)

if __name__ == '__main__':

    executor.start_polling(dp, skip_updates=True)