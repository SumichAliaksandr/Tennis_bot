#Утро — с 06:00 до 12:00 часов (часть суток после пробуждения).
#День — с 12:00 до 18:00 часов (пик рабочей активности).
#Вечер — с 18:00 до 00:00 часов (время отдыха после работы).
#Ночь — с 00:00 до 06:00 часов (время сна).
# в 20.20 дневной прогноз уже на следующий день
from random import random

import requests
import sqlite3
from datetime import datetime

from sfunc import data_plus_


def pogoda_sytki():
    #r = requests.get('https://www.pogoda.by/meteoinformer/js/26825_1.js')
    r = requests.get('https://www.pogoda.by/meteoinformer/js/26820_1.js')
    st0 = r.text
    print(st0)

    i = st0.find('Утро')
    j = st0.find('День')
    k = st0.find('Вечер')
    m = st0.find('Ночь')
    n = st0.rfind('м/с') + 3
    st1 = []

    st1.append(st0[i:j])
    st1.append(st0[j:k])
    st1.append(st0[k:m])
    st1.append(st0[m:n])


    st11 = []
    for i in range(4):

        st1[i] = st1[i].replace('<div title=', '')
        st1[i] = st1[i].replace('</span></td></tr><tr><td>', '')
        st1[i] = st1[i].replace('</div>', '')

        st1[i] = st1[i].replace('\\', '')
        st1[i] = st1[i].replace('"', '')

        st1[i] = st1[i].replace(' <span title=', '')
        st1[i] = st1[i].replace('.>SCTd.png', '')
        st1[i] = st1[i].replace('>', ',')


        pogoda_vremya_sytok = st1[i].split('</td,<td,')
        osadki = pogoda_vremya_sytok[2]
        pogoda_vremya_sytok[2] = osadki[0:osadki.find('.,')] + '.'
        st11.append(pogoda_vremya_sytok)


    ytro = st11[0]
    den = st11[1]
    vecher = st11[2]
    noch = st11[3]
    mes = ytro[0] + ':  ' + ytro[1] + '\n' + ytro[2] + '\nВетер: ' + ytro[3] + '\n'+ '\n'
    mes = mes + den[0] + ':  ' + den[1] + '\n' + den[2] + '\nВетер: ' + den[3] + '\n'+ '\n'
    mes = mes + vecher[0] + ':  ' + vecher[1] + '\n' + vecher[2] + '\nВетер: ' + vecher[3] + '\n'+ '\n'
    mes = mes + noch[0] + ':  ' + noch[1] + '\n' + noch[2] + '\nВетер: ' + noch[3] + '\n'+ '\n' + "Информация сайта \nhttps://www.pogoda.by"

    return mes


def zapolnenie_bazy_pogody():
    print('Zapolnenie bazy pogody')
    r = requests.get('https://www.pogoda.by/meteoinformer/js/26820_1.js')
    st0 = r.text
    i = st0.find('<tr><td colspan=4><u>')
    data = st0[i+21:i+26]
    i = st0.find('°C')
    t_ytro = st0[i-2:i]
    if t_ytro[0] == '.':
        t_ytro = t_ytro[1:]
    st0 = st0[i+10:]
    osadki_ytro = st0[0:st0.find('.png')]
    rain_ytro = osadki_ytro.find('дождь')
    if rain_ytro == -1:
        rain_ytro = 0
    else:
        rain_ytro = 1

    i = st0.find('°C')
    t_den = st0[i - 2:i]
    if t_den[0] == '.':
        t_den = t_den[1:]

    st0 = st0[i + 10:]
    osadki_den = st0[0:st0.find('.png')]
    rain_den = osadki_den.find('дождь')
    if rain_den == -1:
        rain_den = 0
    else:
        rain_den = 1


    i = st0.find('°C')
    t_vecher = st0[i - 2:i]
    if t_vecher[0] == '.':
        t_vecher = t_vecher[1:]

    st0 = st0[i + 10:]
    osadki_vecher = st0[0:st0.find('.png')]
    rain_vecher = osadki_vecher.find('дождь')
    if rain_vecher == -1:
        rain_vecher = 0
    else:
        rain_vecher = 1

    for i in range(8,12):
        conn = sqlite3.connect('baza.db')
        cur = conn.cursor()
        pogoda = (data, i, t_ytro, rain_ytro)

        cur.execute("INSERT INTO pogoda (data, vremia, temperatyra, rain) VALUES(?, ?, ?, ?);", pogoda)
        conn.commit()
    for i in range(12,18):
        conn = sqlite3.connect('baza.db')
        cur = conn.cursor()
        pogoda = (data, i, t_den, rain_den)

        cur.execute("INSERT INTO pogoda (data, vremia, temperatyra, rain) VALUES(?, ?, ?, ?);", pogoda)
        conn.commit()
    for i in range(18,22):
        conn = sqlite3.connect('baza.db')
        cur = conn.cursor()
        pogoda = (data, i, t_vecher, rain_vecher)

        cur.execute("INSERT INTO pogoda (data, vremia, temperatyra, rain) VALUES(?, ?, ?, ?);", pogoda)
        conn.commit()

def pogoda_na_(data):
    try:
        conn = sqlite3.connect('baza.db')
        cur = conn.cursor()
        cur.execute("SELECT vremia, temperatyra, rain FROM pogoda WHERE data=?", ((data),))

        result = cur.fetchall()
        conn.commit()
        return result
    except:
        return 'Данные о погоде отсутствуют'

def pogoda_na_6_dney():
    print('Вносим в базу погоду на 6 дней')
    conn = sqlite3.connect('baza.db')
    cur = conn.cursor()
    cur.execute("DELETE FROM pogoda")
    conn.commit()


    now = datetime.now()
    data = now.strftime("%d.%m")
    chas = int(now.strftime("%H"))
    r = requests.get('http://pda.pogoda.by/?city=26820')
    st0 = r.text


    h = int(st0.find("align='left' alt='погода'/>"))
    st0 = st0[h:]
    pogoda = []
    for i in range (0, 20):
        dogd1 = int(st0.find("align='left' alt='погода'/>"))
        st0 = st0[(dogd1):]
        dogd2 = int(st0.find('Температура воздуха'))

        dog = st0[0:dogd2]

        if dog.find('дождь') == -1:
            dogd = 0
        else:
            dogd = 1

        temp1 = st0.find('°C')
        temp2 = temp1 - 2

        if st0[temp2] == '+' or st0[temp2] == '-':
            temp2 = temp2 - 1
        if st0[temp2] == '.':
            temperatura = int(st0[temp1-1])
        else:
            temperatura = int(st0[temp2:temp1])
        if i == 0:
            for h in range(chas, 24):
                pogoda.append((data, h, temperatura, dogd))
        else:
            if i % 4 == 1:
                data = data_plus_(data, 1)
                hour = 0

            for z in range (0, 6):
                pogoda.append((data, hour, temperatura, dogd))
                hour += 1

        st0 = st0[(temp1+3):]

    for pogod in pogoda:
        conn = sqlite3.connect('baza.db')
        cur = conn.cursor()
        pogoda = (pogod[0], pogod[1], pogod[2], pogod[3])
        cur.execute("INSERT INTO pogoda (data, vremia, temperatyra, rain) VALUES(?, ?, ?, ?);", pogoda)
        conn.commit()

#pogoda_na_6_dney()


#zapolnenie_bazy_pogody()
