import asyncio
import sqlite3
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
from datetime import timedelta
from datetime import datetime
from aiogram import Bot, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram import Dispatcher
from pogoda import pogoda_na_
from sfunc import vnesenie_v_bazy_usera, fraza, fraza_do_vvoda_dannyx, naznachennye_trenirovki, \
    informacia_o_trenirovke, redaktirovanie_trenirovki, user_zapis_otmena_trenirovki, \
    user_zapisalsya_na_trenirovki, zapisalis_na_trenirovky, data_vremia_trenirovki_po_nomery, vnesenie_v_bazy_id_knopok, \
    id_knopok_dlya_redaktirovaniya, mes_to_del_zapis, mes_to_del_info, den_nedeli

f = open('token3.txt', 'r')
for line in f:
    API_TOKEN = line
f.close()

id_trenera = 1227721841
#id_trenera = 1227721842

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

nomer_trenirovki_dlya_redaktirovaniya = 0
data_trenirovki_dlya_redaktirovaniya = '01.01'
vremia_trenirovki_dlya_redaktirovaniya = 0

knopki_naznachit_otmenit_trenirovky_id = 0
data_zapisi_trener = '01.01'


async def chistki(user, dp: Dispatcher):
    conn = sqlite3.connect('baza.db')
    cur = conn.cursor()
    cur.execute("SELECT id_soobscheniya FROM soobscheniya_chistki WHERE id_telegram=?", (user,))
    mes_to_del = cur.fetchall()
    conn.commit()
    for mess in mes_to_del:
        try:
            await bot.delete_message(user, mess[0])
        except: pass
    conn = sqlite3.connect('baza.db')
    cur = conn.cursor()
    cur.execute("DELETE FROM soobscheniya_chistki WHERE id_telegram=? ", (user,))
    conn.commit()

async def chistki_info(dp: Dispatcher):
    conn = sqlite3.connect('baza.db')
    cur = conn.cursor()
    cur.execute("SELECT id_telegram, id_soobscheniya FROM soobscheniya_info")
    mes_to_del = cur.fetchall()
    conn.commit()
    for mess in mes_to_del:
        try:
            await bot.delete_message(mess[0], mess[1])
        except: pass
    conn = sqlite3.connect('baza.db')
    cur = conn.cursor()
    cur.execute("DELETE FROM soobscheniya_info")
    conn.commit()

async def vvod_dannyx_klienta(user, dp: Dispatcher):
    keyboard_markup = types.InlineKeyboardMarkup(row_width=5)
    # default row_width is 3, so here we can omit it actually
    # kept for clearness

    text_and_data = (('Русский', 'russian'),)

    # in real life for the callback_data the callback data factory should be used
    # here the raw string is used for the simplicity
    row_btns = (types.InlineKeyboardButton(text, callback_data=data) for text, data in text_and_data)
    keyboard_markup.row(*row_btns)
    text_and_data = (('Polski', 'poland'),)
    # in real life for the callback_data the callback data factory should be used
    # here the raw string is used for the simplicity
    row_btns = (types.InlineKeyboardButton(text, callback_data=data) for text, data in text_and_data)
    keyboard_markup.row(*row_btns)
    await bot.send_message(user, "Выберите язык\n Wybierz język", reply_markup=keyboard_markup)

    # States
    class Form_reg(StatesGroup):
        yazyk = State()
        name = State()
        photo = State()
        kontakt = State()

    await Form_reg.yazyk.set()

    @dp.callback_query_handler(state=Form_reg.yazyk)
    async def inline_kb_answer_callback_handler(query: types.CallbackQuery, state: FSMContext):

        answer_data = query.data
        user = query.from_user.id
        await query.message.delete()
        print('Выбран язык', query.data)

        # always answer callback queries, even if you have nothing to say
        await query.answer(f'{answer_data!r}')

        async with state.proxy() as data_r:
            data_r['user'] = user
            data_r['yazyk'] = answer_data
            await bot.send_message(user, fraza_do_vvoda_dannyx(3, data_r['yazyk']))
            await Form_reg.name.set()

    @dp.message_handler(state=Form_reg.name)
    async def scan_message(message: types.Message, state: FSMContext):
        async with state.proxy() as data_r:
            data_r['name'] = message.text
            print(data_r['name'])
            await bot.send_message(data_r['user'], fraza_do_vvoda_dannyx(4, data_r['yazyk']))
        await Form_reg.photo.set()

    @dp.message_handler(state=Form_reg.photo, content_types=['photo'])
    async def scan_message(message: types.Message, state: FSMContext):
        async with state.proxy() as data_r:
            data_r['photo_id'] = message.photo[-1].file_id
            print('Photo_id: ', data_r['photo_id'])
            markup_request = ReplyKeyboardMarkup(resize_keyboard=True).add(
            KeyboardButton(fraza_do_vvoda_dannyx(2, data_r['yazyk']), request_contact=True))
            await bot.send_message(data_r['user'], fraza_do_vvoda_dannyx(1, data_r['yazyk']), reply_markup=markup_request)
            await Form_reg.kontakt.set()

    @dp.message_handler(state=Form_reg.kontakt, content_types=types.ContentType.CONTACT)
    async def scan_message(message: types.Message, state: FSMContext):
        print('Хендлер на контакт сработал')
        telephon = message.contact.phone_number
        user = message.from_user.id
        if telephon[0] != '+':
            telephon = '+' + telephon
        print(telephon)

        async with state.proxy() as data_r:
            data_r['telephon'] = telephon

            print(data_r['telephon'])
            try:
                vnesenie_v_bazy_usera(data_r['user'], data_r['name'], data_r['telephon'], data_r['photo_id'], data_r['yazyk'])
                await bot.send_message(data_r['user'], fraza(5, data_r['user']), reply_markup=ReplyKeyboardRemove())
            except:
                print('Не получилось внести в базу')
        await state.finish()
        now = datetime.now()
        data_zapisi = now.strftime("%d.%m")
        await knopki_klienta(user, '0', data_zapisi, dp)

async def novyi_adres(dp:Dispatcher):

    class Form_na(StatesGroup):
        Novyi_adres = State()

    await Form_na.Novyi_adres.set()
    await chistki(id_trenera,dp)
    mes = await bot.send_message(id_trenera, "Введите новый адрес.")

    mes_to_del_zapis(id_trenera, mes.message_id)

    @dp.message_handler(state=Form_na.Novyi_adres)
    async def process_name1(message: types.Message, state: FSMContext):
        print('Новый адрес:', message.text)
        znachenie = message.text
        id = message.message_id
        await bot.delete_message(id_trenera, id)
        redaktirovanie_trenirovki(nomer_trenirovki_dlya_redaktirovaniya, 'adres', znachenie)
        conn = sqlite3.connect('baza.db')
        cur = conn.cursor()
        cur.execute("SELECT telegram_id FROM zapis_na_trenirovky WHERE nomer_trenirovki=?", (nomer_trenirovki_dlya_redaktirovaniya,))
        result = cur.fetchall()
        conn.commit()
        print('ИД-шники записавшихся на тренировку: ', result)
        data_vremia = data_vremia_trenirovki_po_nomery(nomer_trenirovki_dlya_redaktirovaniya)

        if result != []:
            for id in result:
                mes = await bot.send_message(id[0], fraza(10, id[0]) + str(data_vremia[0]) + ' ' + str(data_vremia[1]) + ':00 ' + fraza(11, id[0]) + znachenie)
                mes_to_del_info(id[0], mes.message_id)
        print('ввели новый адрес')
        await podrobnee(vremia_trenirovki_dlya_redaktirovaniya, data_trenirovki_dlya_redaktirovaniya, dp)

async def message_vsem_novaya_trenirovka(mes,dp: Dispatcher):
    conn = sqlite3.connect('baza.db')
    cur = conn.cursor()
    cur.execute("SELECT telegram_id FROM klienty ")
    result = cur.fetchall()
    conn.commit()

    for user in result:
        if user[0] != id_trenera:

            msg = fraza(8, user[0]) + str(mes[0]) + '  ' + str(mes[1]) + ':00'
            try:
                soob = await bot.send_message(user[0], msg)
                mes_to_del_info(user[0], soob.message_id)
                await asyncio.sleep(.05)

            except:
                pass


async def naznachit_otmenit_trenirovky(vremia, data, dp:Dispatcher):

    conn = sqlite3.connect('baza.db')
    cur = conn.cursor()

    cur.execute("SELECT nomer FROM trenirovki WHERE data=? and vremia=?", (data, vremia))
    result = cur.fetchall()
    conn.commit()

    if result == []:
        conn = sqlite3.connect('baza.db')
        cur = conn.cursor()
        trenirovka = ('СШ38',  data, vremia, 40, 2, 4)
        cur.execute("INSERT INTO trenirovki(adres, data, vremia, zena, min_chelovek, max_chelovek) VALUES(?, ?, ?, ?, ?, ?);", trenirovka)
        conn.commit()
        mes = (data, vremia)
        await message_vsem_novaya_trenirovka(mes,dp)
    else:
        conn = sqlite3.connect('baza.db')
        cur = conn.cursor()
        cur.execute("DELETE FROM trenirovki WHERE data=? and vremia=?", (data, vremia))
        conn.commit()
        nomer_ydalyaemoi_trenirovki = result[0]
        print('Номер удаляемой тренировки: ', nomer_ydalyaemoi_trenirovki)
        conn = sqlite3.connect('baza.db')
        cur = conn.cursor()
        cur.execute("SELECT telegram_id FROM zapis_na_trenirovky WHERE nomer_trenirovki=?", nomer_ydalyaemoi_trenirovki)
        result = cur.fetchall()
        conn.commit()
        print('ИД-шники записавшихся на тренировку: ', result)

        if result !=[]:
            for id in result:
                mes = await bot.send_message(id[0], fraza(9, id[0]) + str(data) + ' ' + str(vremia) + ':00',disable_notification=True)
                mes_to_del_info(id[0], mes.message_id)
        conn = sqlite3.connect('baza.db')
        cur = conn.cursor()
        cur.execute("DELETE FROM zapis_na_trenirovky WHERE nomer_trenirovki=?", nomer_ydalyaemoi_trenirovki)
        conn.commit()



async def podrobnee(vremia, data_zapisi, dp:Dispatcher):

    await chistki(id_trenera, dp)

    info = informacia_o_trenirovke(vremia, data_zapisi)

    global nomer_trenirovki_dlya_redaktirovaniya
    nomer_trenirovki_dlya_redaktirovaniya = int(info[0])

    global data_trenirovki_dlya_redaktirovaniya
    data_trenirovki_dlya_redaktirovaniya = data_zapisi

    global vremia_trenirovki_dlya_redaktirovaniya
    vremia_trenirovki_dlya_redaktirovaniya = vremia

    klienty = zapisalis_na_trenirovky(info[0])
    if klienty != []:
        for klient in klienty:
            mes = await bot.send_photo(id_trenera, klient[1], caption=('Записался клиент: ' + klient[0]))

            mes_to_del_zapis(id_trenera, mes.message_id)

    mes = await bot.send_message(id_trenera, 'Если нужно изменить настройки - нажмите на соответствующую кнопку')

    mes_to_del_zapis(id_trenera, mes.message_id)

    knopka = 'Изменить'
    keyboard_markup = types.InlineKeyboardMarkup(row_width=5)
    text_and_data = ((knopka, 'Adres'), )
    row_btns = (types.InlineKeyboardButton(text, callback_data=data) for text, data in text_and_data)
    keyboard_markup.row(*row_btns)
    mes = await bot.send_message(id_trenera, 'Адрес: ' + str(info[1]), reply_markup=keyboard_markup)

    mes_to_del_zapis(id_trenera, mes.message_id)

    knopka = 'Изменить'
    keyboard_markup = types.InlineKeyboardMarkup(row_width=5)
    text_and_data = ((knopka, 'zena'),)
    row_btns = (types.InlineKeyboardButton(text, callback_data=data) for text, data in text_and_data)
    keyboard_markup.row(*row_btns)
    mes = await bot.send_message(id_trenera, 'Цена: ' + str(info[2]), reply_markup=keyboard_markup)

    mes_to_del_zapis(id_trenera, mes.message_id)

    knopka = 'Изменить'
    keyboard_markup = types.InlineKeyboardMarkup(row_width=5)
    text_and_data = ((knopka, 'min_chelovek'),)
    row_btns = (types.InlineKeyboardButton(text, callback_data=data) for text, data in text_and_data)
    keyboard_markup.row(*row_btns)
    mes = await bot.send_message(id_trenera, 'Минимальное количество человек, при котором состоится тренировка: '
                           + str(info[3]), reply_markup=keyboard_markup)

    mes_to_del_zapis(id_trenera, mes.message_id)

    knopka = 'Изменить'
    keyboard_markup = types.InlineKeyboardMarkup(row_width=5)
    text_and_data = ((knopka, 'max_chelovek'),)
    row_btns = (types.InlineKeyboardButton(text, callback_data=data) for text, data in text_and_data)
    keyboard_markup.row(*row_btns)

    mes = await bot.send_message(id_trenera, 'Максимальное количество человек, которые могут записаться на тренировку: '
                           + str(info[4]), reply_markup=keyboard_markup)

    mes_to_del_zapis(id_trenera, mes.message_id)

    knopka = 'Назад'
    keyboard_markup = types.InlineKeyboardMarkup(row_width=5)
    text_and_data = ((knopka, 'nazad'),)
    row_btns = (types.InlineKeyboardButton(text, callback_data=data) for text, data in text_and_data)
    keyboard_markup.row(*row_btns)
    mes = await bot.send_message(id_trenera, 'Вернуться к тренировкам', reply_markup=keyboard_markup)

    mes_to_del_zapis(id_trenera, mes.message_id)

    # States
    class Form_p(StatesGroup):
        Podrobnee = State()

    await Form_p.Podrobnee.set()

    @dp.callback_query_handler(state=Form_p.Podrobnee, text='nazad')
    async def inline_kb_answer_callback_handler(query: types.CallbackQuery, state: FSMContext):
        now = datetime.now()
        data = now.strftime("%d.%m")
        await chistki(id_trenera, dp)
        await naznachit_trenirovky(id_trenera, '0', data, dp)

    @dp.callback_query_handler(state=Form_p.Podrobnee)
    async def inline_kb_answer_callback_handler(query: types.CallbackQuery, state: FSMContext):


        answer_data = query.data
        # always answer callback queries, even if you have nothing to say
        await query.answer(f'Вы выбрали {answer_data!r}')
        print(answer_data)
        Adres = answer_data.find('Adres')
        await chistki(id_trenera, dp)
        if Adres != -1:
            await novyi_adres(dp)
            print('работаем дальше')


        zena = answer_data.find('zena')
        if zena != -1:
            # States
            class Form(StatesGroup):
                Novyi_zena = State()

            mes = await bot.send_message(query.from_user.id, "Введите новую цену цифрами.")

            mes_to_del_zapis(id_trenera, mes.message_id)

            await Form.Novyi_zena.set()

            @dp.message_handler(state=Form.Novyi_zena)
            async def process_name(message: types.Message, state: FSMContext):
                id = message.message_id
                await bot.delete_message(id_trenera, id)

                znachenie = message.text
                if znachenie.isdigit():
                    redaktirovanie_trenirovki(nomer_trenirovki_dlya_redaktirovaniya, 'zena', znachenie)
                    await podrobnee(vremia_trenirovki_dlya_redaktirovaniya, data_trenirovki_dlya_redaktirovaniya, dp)
                else:
                    mes = await bot.send_message(id_trenera, 'Цена должна состоять из цифр. Вы ввели: ' + znachenie)
                    mes_to_del_zapis(id_trenera, mes.message_id)
                    await asyncio.sleep(5)
                    await podrobnee(vremia_trenirovki_dlya_redaktirovaniya, data_trenirovki_dlya_redaktirovaniya, dp)

        min_chelovek = answer_data.find('min_chelovek')
        if min_chelovek != -1:
            # States
            class Form(StatesGroup):
                Novyi_min_chelovek = State()

            mes = await bot.send_message(query.from_user.id, "Введите цифрами минимальное количество человек, при котором состоится тренировка.")

            mes_to_del_zapis(id_trenera, mes.message_id)
            await Form.Novyi_min_chelovek.set()

            @dp.message_handler(state=Form.Novyi_min_chelovek)
            async def process_name(message: types.Message, state: FSMContext):
                id = message.message_id
                await bot.delete_message(id_trenera, id)

                znachenie = message.text
                if znachenie.isdigit():
                    redaktirovanie_trenirovki(nomer_trenirovki_dlya_redaktirovaniya, 'min_chelovek', znachenie)
                    await podrobnee(vremia_trenirovki_dlya_redaktirovaniya, data_trenirovki_dlya_redaktirovaniya, dp)
                else:
                    mes = await bot.send_message(id_trenera, 'Минимальное количество человек должно вводиться цифрами. Вы ввели: ' + znachenie)
                    mes_to_del_zapis(id_trenera, mes.message_id)
                    await asyncio.sleep(5)
                    await podrobnee(vremia_trenirovki_dlya_redaktirovaniya, data_trenirovki_dlya_redaktirovaniya, dp)

        max_chelovek = answer_data.find('max_chelovek')
        if max_chelovek != -1:
            # States
            class Form(StatesGroup):
                Novyi_max_chelovek = State()

            mes = await bot.send_message(query.from_user.id,
                                         "Введите максимальное количество человек, которые могут записаться на тренировку.")

            mes_to_del_zapis(id_trenera, mes.message_id)
            await Form.Novyi_max_chelovek.set()

            @dp.message_handler(state=Form.Novyi_max_chelovek)
            async def process_name(message: types.Message, state: FSMContext):
                id = message.message_id
                await bot.delete_message(id_trenera, id)

                znachenie = message.text
                if znachenie.isdigit():
                    redaktirovanie_trenirovki(nomer_trenirovki_dlya_redaktirovaniya, 'max_chelovek', znachenie)
                    await podrobnee(vremia_trenirovki_dlya_redaktirovaniya, data_trenirovki_dlya_redaktirovaniya, dp)
                else:
                    mes = await bot.send_message(id_trenera, 'Максимальное количество человек должно вводиться цифрами. Вы ввели: ' + znachenie)
                    mes_to_del_zapis(id_trenera, mes.message_id)
                    await asyncio.sleep(5)
                    await podrobnee(vremia_trenirovki_dlya_redaktirovaniya, data_trenirovki_dlya_redaktirovaniya, dp)


        #await state.finish()

async def user_podrobnee(user, vremia, data_zapisi, dp):

    print(user, vremia, data_zapisi)
    info = informacia_o_trenirovke(vremia, data_zapisi)
    print(info)
    if info[5] != 0:
        zena = str(round(info[2]/info[5]))
    else:
        zena = str(round(info[2]))
    poslanie = fraza(14, user) + info[1] + fraza(15, user) \
               + str(info[5]) + fraza(16, user) + zena + fraza(17, user) + \
               str(info[4] - info[5]) + fraza(18, user) + str(info[3]) + fraza(19, user)

    klienty = zapisalis_na_trenirovky(info[0])
    if klienty != []:
        for klient in klienty:
            mes = await bot.send_photo(user, klient[1], caption=klient[0])

            mes_to_del_zapis(user, mes.message_id)
    knopka = '⬅️'
    keyboard_markup = types.InlineKeyboardMarkup(row_width=5)
    text_and_data = ((knopka, 'nazad'),)
    row_btns = (types.InlineKeyboardButton(text, callback_data=data) for text, data in text_and_data)
    keyboard_markup.row(*row_btns)
    mes = await bot.send_message(user, poslanie, reply_markup=keyboard_markup)

    mes_to_del_zapis(user, mes.message_id)

    @dp.callback_query_handler(text='nazad')
    async def inline_kb_answer_callback_handler(query: types.CallbackQuery, state: FSMContext):
        await query.answer()
        now = datetime.now()
        data = now.strftime("%d.%m")
        user = query.from_user.id
        await chistki(user, dp)
        await knopki_klienta(user, '0', data, dp)

async def naznachit_trenirovky(user, mes_id_to_edit, data_zapisi, dp:Dispatcher):
    print('470', user, mes_id_to_edit, data_zapisi)

    now = datetime.now()
    data = now.strftime("%d.%m")
    chas = int(now.strftime("%H"))

    # States
    class Form(StatesGroup):

        Vybor = State()

    await Form.Vybor.set()

    trenirovki = naznachennye_trenirovki(data_zapisi)
    pogoda = pogoda_na_(data_zapisi)

    if data == data_zapisi:
        if chas >= 8:
            a = int(chas)
        else:
            a = 8
        mes = 'Тренировки сегодня'
    else:
        a = 8
        mes = 'Тренировки ' + data_zapisi + '. ' + den_nedeli(data_zapisi, user)

    keyboard_markup = types.InlineKeyboardMarkup(row_width=5)

    for i in range(a,22):
        knopka = ''
        if trenirovki != None:
            for tren in trenirovki:
                if tren[0] == i:
                    knopka = '✅'


        knopka = knopka + str(i) + 'ч '
        if pogoda != 'Данные о погоде отсутствуют':
            for pog in pogoda:

                if pog[0] == i:
                    knopka = knopka + str(pog[1]) + '°C '
                    if pog[2] == 0:
                        knopka = knopka + '☀'
                    else: knopka = knopka + '💦'

        info = informacia_o_trenirovke(i, data_zapisi)
        if info!=[]:
            informacia = str(info[5])+'🧒'
            text_and_data = ((knopka + informacia, str(data_zapisi) + 'tr' + str(i)) , ('Изменить', str(data_zapisi) + 'tp' + str(i)))
        else:
            text_and_data = ((knopka, str(data_zapisi) + 'tr' + str(i)), )


        # in real life for the callback_data the callback data factory should be used
        # here the raw string is used for the simplicity
        row_btns = (types.InlineKeyboardButton(text, callback_data=data) for text, data in text_and_data)
        keyboard_markup.row(*row_btns)
    if data == data_zapisi:
        text_and_data = (('Меню', 'menu'), ('➡', str(data_zapisi) + 'right'))

    else:
        text_and_data = (('⬅', str(data_zapisi) + 'left'), ('Меню', 'menu'), ('➡', str(data_zapisi) + 'right'))

    # in real life for the callback_data the callback data factory should be used
    # here the raw string is used for the simplicity
    row_btns = (types.InlineKeyboardButton(text, callback_data=data) for text, data in text_and_data)
    keyboard_markup.row(*row_btns)

    if mes_id_to_edit !='0':
        await bot.edit_message_text(mes, user, message_id=mes_id_to_edit, reply_markup=keyboard_markup)
        """""""""""
        try:
            #await bot.delete_message(user, mes_id_to_edit)
            print('543', mes_id_to_edit)
            await bot.edit_message_text(mes, user, message_id=mes_id_to_edit, reply_markup=keyboard_markup)
            #await bot.edit_message_reply_markup(user, message_id=mes_id_to_edit, )

        except:
            print('То же самое сообщение')
            """""""""""
    else:
        sms = await bot.send_message(user, mes, reply_markup=keyboard_markup)
        vnesenie_v_bazy_id_knopok(id_trenera, sms.message_id)


    @dp.callback_query_handler(state=Form.Vybor)
    async def inline_kb_answer_callback_handler(query: types.CallbackQuery, state: FSMContext):
        global knopki_naznachit_otmenit_trenirovky_id
        global data_zapisi_trener
        await query.answer()

        answer_data = query.data
        mes_id_to_edit = query.message.message_id
        knopki_naznachit_otmenit_trenirovky_id = query.message.message_id
        vnesenie_v_bazy_id_knopok(id_trenera, query.message.message_id)
        user = query.from_user.id
        data_zapisi = answer_data[0:5]
        print('560', data_zapisi_trener, data_zapisi[0:2])
        stroka = ''
        stroka = data_zapisi[0:2]
        if stroka.isdigit():
            data_zapisi_trener = stroka
        else:
            now = datetime.now()
            data_zapisi_trener = now.strftime("%d.%m")
            print('дата записи неправильная 565')
        print('566', data_zapisi_trener)

        tr = answer_data.find('tr')
        if tr !=-1:
            vremia = int(answer_data[tr+2:])
            await naznachit_otmenit_trenirovky(vremia, data_zapisi, dp)

        tp = answer_data.find('tp')
        if tp != -1:
            vremia = int(answer_data[tp + 2:])
            await query.message.delete()
            await state.finish()
            await podrobnee(vremia, data_zapisi, dp)
        else:

            if (answer_data != 'menu'):
                now = datetime.now()
                year = int(now.strftime("%y"))
                chislo_mesuaca = int(answer_data[0:2])

                mesyac = int(answer_data[3:5])

                data_zapisi = datetime(year, mesyac, chislo_mesuaca)
                if answer_data.find('left') != -1:
                    data_zapisi += - timedelta(days=1)
                if answer_data.find('right') != -1:
                    data_zapisi += timedelta(days=1)
                data_zapisi = data_zapisi.strftime("%d.%m")

                if tp == -1:
                    await naznachit_trenirovky(user, mes_id_to_edit, data_zapisi, dp)
            else:
                await query.message.delete()
                await state.finish()
                await knopki_trenera(user, dp)


async def knopki_trenera(user, dp: Dispatcher):
    print('Тренеру отправлены кнопки')
    keyboard_markup = types.InlineKeyboardMarkup(row_width=5)
    # default row_width is 3, so here we can omit it actually
    # kept for clearness

    text_and_data = (('Тренировки', '1t'),)
    # in real life for the callback_data the callback data factory should be used
    # here the raw string is used for the simplicity
    row_btns = (types.InlineKeyboardButton(text, callback_data=data) for text, data in text_and_data)
    keyboard_markup.row(*row_btns)

    text_and_data = (('Сообщение клиентам', '2t'),)
    # in real life for the callback_data the callback data factory should be used
    # here the raw string is used for the simplicity
    row_btns = (types.InlineKeyboardButton(text, callback_data=data) for text, data in text_and_data)
    keyboard_markup.row(*row_btns)

    await bot.send_message(user, "Добро пожаловать!", reply_markup=keyboard_markup)

    @dp.callback_query_handler(text='1t')
    @dp.callback_query_handler(text='2t')
    async def inline_kb_answer_callback_handler(query: types.CallbackQuery):
        answer_data = query.data
        knopka = query.message.text
        # always answer callback queries, even if you have nothing to say
        await query.answer(f'Вы выбрали {knopka!r}')
        await query.message.delete()

#Назначить тренировку
        if answer_data == '1t':
            now = datetime.now()
            data = now.strftime("%d.%m")
            await naznachit_trenirovky(id_trenera, '0', data, dp)
        if answer_data == '2t':
            await zamena_knopok(dp)

async def knopki_klienta(user, mes_id_to_edit, data_zapisi, dp: Dispatcher):
    vnesenie_v_bazy_id_knopok(user, int(mes_id_to_edit))
    now = datetime.now()
    data = now.strftime("%d.%m")
    chas = int(now.strftime("%H"))

    if data == data_zapisi:
        mes = '🎾 ' + fraza(13, user)

    else:
        mes = '🎾 ' + data_zapisi + '. ' + den_nedeli(data_zapisi, user)

    # States
    class Formk(StatesGroup):

        Vybor_klient = State()

    await Formk.Vybor_klient.set()
    trenirovki = naznachennye_trenirovki(data_zapisi)
    pogoda = pogoda_na_(data_zapisi)
    trenirovki_user = user_zapisalsya_na_trenirovki(user)

    keyboard_markup = types.InlineKeyboardMarkup(row_width=5)
    print('Назначенные тренировки ', trenirovki)
    if trenirovki != []:
        for trenirovka in trenirovki:

            trenirovka = trenirovka[0]
            if (trenirovka >= chas) or (data != data_zapisi):
                knopka = ''

                if trenirovki_user != []:
                    for tren_user in trenirovki_user:

                        #if (tren_user[1] == data_zapisi) and (tren_user[2] == trenirovka):
                        if (str(tren_user[1]) == str(data_zapisi)) and (tren_user[2] == trenirovka):
                            knopka = knopka + '✅'


                knopka = knopka + str(trenirovka) + ':00; '
                if pogoda != 'Данные о погоде отсутствуют':
                    for pog in pogoda:

                        if pog[0] == trenirovka:
                            knopka = knopka + str(pog[1]) + '°C '
                            if pog[2] == 0:
                                knopka = knopka + '☀'
                            else:
                                knopka = knopka + '💦'

                info = informacia_o_trenirovke(trenirovka, data_zapisi)
                if info != []:
                    informacia = str(info[5]) + '🧒'
                    text_and_data = (
                    (knopka + informacia, str(data_zapisi) + 'tr' + str(trenirovka)), (fraza(7, user), str(data_zapisi) + 'tp' + str(trenirovka)))
                else:
                    text_and_data = ((knopka, str(data_zapisi) + 'tr' + str(trenirovka)),)

                # in real life for the callback_data the callback data factory should be used
                # here the raw string is used for the simplicity
                row_btns = (types.InlineKeyboardButton(text, callback_data=data) for text, data in text_and_data)
                keyboard_markup.row(*row_btns)

        if data >= data_zapisi:
            text_and_data = (('➡', str(data_zapisi) + 'right'),)

        else:
            text_and_data = (('⬅', str(data_zapisi) + 'left'), ('➡', str(data_zapisi) + 'right'))

        # in real life for the callback_data the callback data factory should be used
        # here the raw string is used for the simplicity
        row_btns = (types.InlineKeyboardButton(text, callback_data=data) for text, data in text_and_data)
        keyboard_markup.row(*row_btns)

        if mes_id_to_edit != '0':
            try:
                # await bot.delete_message(user, mes_id_to_edit)
                await bot.edit_message_text(mes, user, message_id=int(mes_id_to_edit), reply_markup=keyboard_markup)
                # await bot.edit_message_reply_markup(user, message_id=mes_id_to_edit, )

            except:
                print('То же самое сообщение')
        else:

            print('user = ', user, 'mes=', mes)
            knopochki = await bot.send_message(user, mes, reply_markup=keyboard_markup)
            print('763 knopochki.message_id', knopochki.message_id)
            vnesenie_v_bazy_id_knopok(user, knopochki.message_id)
            print('763 knopochki.message_id', knopochki.message_id)

    else:
        mes = mes + '. ' + fraza(31, user)
        print('user = ', user, 'mes=', mes)
        if data >= data_zapisi:
            text_and_data = (('➡', str(data_zapisi) + 'right'),)

        else:
            text_and_data = (('⬅', str(data_zapisi) + 'left'), ('➡', str(data_zapisi) + 'right'))

        # in real life for the callback_data the callback data factory should be used
        # here the raw string is used for the simplicity
        row_btns = (types.InlineKeyboardButton(text, callback_data=data) for text, data in text_and_data)
        keyboard_markup.row(*row_btns)
        if mes_id_to_edit != '0':
            try:
                # await bot.delete_message(user, mes_id_to_edit)
                await bot.edit_message_text(mes, user, message_id=int(mes_id_to_edit), reply_markup=keyboard_markup)
                # await bot.edit_message_reply_markup(user, message_id=mes_id_to_edit, )

            except:
                print('То же самое сообщение')
        else:

            print('user = ', user, 'mes=', mes)
            knopochki = await bot.send_message(user, mes, reply_markup=keyboard_markup)
            print('763 knopochki.message_id', knopochki.message_id)
            vnesenie_v_bazy_id_knopok(user, knopochki.message_id)
            print('763 knopochki.message_id', knopochki.message_id)

    @dp.callback_query_handler(state=Formk.Vybor_klient)
    async def inline_kb_answer_callback_handler(query: types.CallbackQuery, state: FSMContext):
        #await query.answer()
        now = datetime.now()
        data = now.strftime("%d.%m")
        answer_data = query.data
        mes_id_to_edit = query.message.message_id
        user = query.from_user.id
        data_zapisi = answer_data[0:5]

        if answer_data == 'menu':
            print('не тот хендлер')
            await query.message.delete()
            await naznachit_trenirovky(id_trenera, '0', data, dp)
        else:
            tr = answer_data.find('tr')
            if tr != -1:
                vremia = int(answer_data[tr + 2:])
                zapis = user_zapis_otmena_trenirovki(user, vremia, data_zapisi)
                if zapis:
                    await query.answer()
                else:
                    await query.answer(fraza(12, user))

            tp = answer_data.find('tp')
            if tp != -1:
                await query.answer()

                vremia = int(answer_data[tp + 2:])
                await query.message.delete()
                await state.finish()
                await user_podrobnee(user, vremia, data_zapisi, dp)
            else:
                now = datetime.now()
                year = int(now.strftime("%y"))
                chislo_mesuaca = int(answer_data[0:2])

                mesyac = int(answer_data[3:5])

                data_zapisi = datetime(year, mesyac, chislo_mesuaca)
                if answer_data.find('left') != -1:
                    await query.answer()

                    data_zapisi += - timedelta(days=1)
                if answer_data.find('right') != -1:
                    await query.answer()
                    data_zapisi += timedelta(days=1)
                data_zapisi = data_zapisi.strftime("%d.%m")

                if data > data_zapisi:
                    data_zapisi = data
                if tp == -1:
                    await knopki_klienta(user, mes_id_to_edit, data_zapisi, dp)

async def otmena_trenirovok_esli_malo_zapisalos(dp:Dispatcher):
    now = datetime.now()
    data = now.strftime("%d.%m")
    chas = int(now.strftime("%H"))
    chas += 1
    info = informacia_o_trenirovke(chas, data)
    print(data, chas, info)
    if info != []:
        usery = zapisalis_na_trenirovky(info[0])
        print(usery)
        if info[5]<info[3]:
            conn = sqlite3.connect('baza.db')
            cur = conn.cursor()
            cur.execute("DELETE FROM trenirovki WHERE data=? and vremia=?", (data, chas))
            conn.commit()
            nomer_ydalyaemoi_trenirovki = int(info[0])
            print('Номер удаляемой тренировки: ', nomer_ydalyaemoi_trenirovki)
            conn = sqlite3.connect('baza.db')
            cur = conn.cursor()
            cur.execute("SELECT telegram_id FROM zapis_na_trenirovky WHERE nomer_trenirovki=?", (nomer_ydalyaemoi_trenirovki,))
            result = cur.fetchall()
            conn.commit()
            print('ИД-шники записавшихся на тренировку: ', result)

            mes = await bot.send_message(id_trenera, 'Отменена тренировка ' + str(data) + ' ' + str(chas) + ':00. Записалось слишком мало людей')
            mes_to_del_info(id_trenera, mes.message_id)

            await zamena_knopok(dp)


            if result != []:
                for id in result:
                    try:
                        mes = await bot.send_message(id[0], fraza(9, id[0]) + str(data) + ' ' + str(chas) + ':00' + fraza(21, id[0]))
                        mes_to_del_info(id[0], mes.message_id)
                    except: pass
            conn = sqlite3.connect('baza.db')
            cur = conn.cursor()
            cur.execute("DELETE FROM zapis_na_trenirovky WHERE nomer_trenirovki=?", (nomer_ydalyaemoi_trenirovki,))
            conn.commit()

async def napominanie_o_trenirovke_za_1_chas(dp:Dispatcher):
    now = datetime.now()
    data = now.strftime("%d.%m")
    chas = int(now.strftime("%H"))
    chas += 1
    info = informacia_o_trenirovke(chas, data)
    if info != [] and info[5]>0:
        users = zapisalis_na_trenirovky(info[0])
        for user in users:
            mes = await bot.send_message(user[2], fraza(22,user[2]) + str(chas) + ':00' + fraza(23, user[2]) + info[1])
            mes_to_del_info(user[2], mes.message_id)
        mes = await bot.send_message(id_trenera, 'Напоминание о тренировке ' + str(chas) + ':00 ' + 'по адресу: '+ info[1])
        mes_to_del_info(id_trenera, mes.message_id)

async  def zamena_knopok(dp:Dispatcher):
    global knopki_naznachit_otmenit_trenirovky_id

    now = datetime.now()
    data = now.strftime("%d.%m")
    conn = sqlite3.connect('baza.db')
    cur = conn.cursor()
    cur.execute("SELECT telegram_id FROM klienty")
    users = cur.fetchall()
    conn.commit()
    print(users)
    #try:


    now = datetime.now()
    data = now.strftime("%d.%m")
    chas = int(now.strftime("%H"))

    trenirovki = naznachennye_trenirovki(data)
    pogoda = pogoda_na_(data)

    if chas >= 8:
        a = int(chas)
    else:
        a = 8
    mes = 'Тренировки сегодня'


    keyboard_markup = types.InlineKeyboardMarkup(row_width=5)

    for i in range(a, 22):
        knopka = ''
        if trenirovki != None:
            for tren in trenirovki:
                if tren[0] == i:
                    knopka = '✅'

        knopka = knopka + str(i) + 'ч '
        if pogoda != 'Данные о погоде отсутствуют':
            for pog in pogoda:

                if pog[0] == i:
                    knopka = knopka + str(pog[1]) + '°C '
                    if pog[2] == 0:
                        knopka = knopka + '☀'
                    else:
                        knopka = knopka + '💦'

        info = informacia_o_trenirovke(i, data)
        if info != []:
            informacia = str(info[5]) + '🧒'
            text_and_data = (
            (knopka + informacia, str(data) + 'tr' + str(i)), ('Изменить', str(data) + 'tp' + str(i)))
        else:
            text_and_data = ((knopka, str(data) + 'tr' + str(i)),)

        # in real life for the callback_data the callback data factory should be used
        # here the raw string is used for the simplicity
        row_btns = (types.InlineKeyboardButton(text, callback_data=data) for text, data in text_and_data)
        keyboard_markup.row(*row_btns)
    text_and_data = (('Меню', 'menu'), ('➡', str(data) + 'right'))

    # in real life for the callback_data the callback data factory should be used
    # here the raw string is used for the simplicity
    row_btns = (types.InlineKeyboardButton(text, callback_data=data) for text, data in text_and_data)
    keyboard_markup.row(*row_btns)
    try:
        await bot.edit_message_text(mes, id_trenera, message_id=id_knopok_dlya_redaktirovaniya(id_trenera),
                                reply_markup=keyboard_markup)
    except:
        pass
        #await naznachit_trenirovky(id_trenera, '0', data, dp)
        #print('Не заменены кнопки тренера')
    print('877', id_trenera, id_knopok_dlya_redaktirovaniya(id_trenera), data_zapisi_trener)
    #await naznachit_trenirovky(id_trenera, knopki_naznachit_otmenit_trenirovky_id, data_zapisi_trener, dp)
    for user in users:
        user = user[0]
        z = id_knopok_dlya_redaktirovaniya(user)
        if (z!= None) and (user != id_trenera  ):
            #try:
                #await knopki_klienta(user, id_knopok_dlya_redaktirovaniya(user), data, dp)
            #except:
                #print('Не заменены кнопки клиента ', user)
            print('889', user, id_knopok_dlya_redaktirovaniya(user), data)


            now = datetime.now()
            data = now.strftime("%d.%m")
            chas = int(now.strftime("%H"))

            mes = '🎾 ' + fraza(13, user)

            trenirovki = naznachennye_trenirovki(data)
            pogoda = pogoda_na_(data)
            trenirovki_user = user_zapisalsya_na_trenirovki(user)

            keyboard_markup = types.InlineKeyboardMarkup(row_width=5)
            print('Назначенные тренировки ', trenirovki)
            if trenirovki != []:
                for trenirovka in trenirovki:

                    trenirovka = trenirovka[0]
                    if (trenirovka >= chas) or (data != data):
                        knopka = ''

                        if trenirovki_user != []:
                            for tren_user in trenirovki_user:

                                # if (tren_user[1] == data_zapisi) and (tren_user[2] == trenirovka):
                                if (str(tren_user[1]) == str(data)) and (tren_user[2] == trenirovka):
                                    knopka = knopka + '✅'

                        knopka = knopka + str(trenirovka) + ':00; '
                        if pogoda != 'Данные о погоде отсутствуют':
                            for pog in pogoda:

                                if pog[0] == trenirovka:
                                    knopka = knopka + str(pog[1]) + '°C '
                                    if pog[2] == 0:
                                        knopka = knopka + '☀'
                                    else:
                                        knopka = knopka + '💦'

                        info = informacia_o_trenirovke(trenirovka, data)
                        if info != []:
                            informacia = str(info[5]) + '🧒'
                            text_and_data = (
                                (knopka + informacia, str(data) + 'tr' + str(trenirovka)),
                                (fraza(7, user), str(data) + 'tp' + str(trenirovka)))
                        else:
                            text_and_data = ((knopka, str(data) + 'tr' + str(trenirovka)),)

                        # in real life for the callback_data the callback data factory should be used
                        # here the raw string is used for the simplicity
                        row_btns = (types.InlineKeyboardButton(text, callback_data=data) for text, data in
                                    text_and_data)
                        keyboard_markup.row(*row_btns)

                text_and_data = (('➡', str(data) + 'right'),)

                # in real life for the callback_data the callback data factory should be used
                # here the raw string is used for the simplicity
                row_btns = (types.InlineKeyboardButton(text, callback_data=data) for text, data in text_and_data)
                keyboard_markup.row(*row_btns)

                try:
                    await bot.edit_message_text(mes, user, message_id=id_knopok_dlya_redaktirovaniya(user),
                                                reply_markup=keyboard_markup)
                except:
                    pass