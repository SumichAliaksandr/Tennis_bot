import sqlite3
from datetime import datetime, timedelta


def nolik(data):

    data = str(data)
    if data.find('.') == 1:
        data = '0' + data
    return data

def fraza(nomer_frazy, user):
    conn = sqlite3.connect('baza.db')
    cur = conn.cursor()
    cur.execute("SELECT yazyk FROM klienty WHERE telegram_id=?", ((user),))
    result = cur.fetchone()
    conn.commit()
    yazyk = result[0]

    #формируем запрос
    zapros = 'SELECT ' + yazyk + ' FROM nadpisi WHERE nomer=?'
    cur.execute(zapros, ((nomer_frazy),))
    result = cur.fetchone()
    conn.commit()

    return result[0]

def fraza_do_vvoda_dannyx(nomer_frazy, yazyk):
    conn = sqlite3.connect('baza.db')
    cur = conn.cursor()
    zapros = 'SELECT ' + yazyk + ' FROM nadpisi WHERE nomer=?'
    cur.execute(zapros, (nomer_frazy,))
    result = cur.fetchone()
    conn.commit()
    return result[0]

def vnesenie_v_bazy_usera(telegram_id, name, telefon, foto_id, yazyk):
    conn = sqlite3.connect('baza.db')
    cur = conn.cursor()
    user = (telegram_id, name, telefon, foto_id, yazyk)

    cur.execute("INSERT INTO klienty(telegram_id, name, telefon, foto_id, yazyk) VALUES(?, ?, ?, ?, ?);", user)
    conn.commit()

def user_v_baze(user):
    conn = sqlite3.connect('baza.db')
    cur = conn.cursor()
    cur.execute("SELECT name FROM klienty WHERE telegram_id=?", ((user),))
    result = cur.fetchone()
    conn.commit()

    if result == None:
        return False
    else:
        return True

def naznachennye_trenirovki(data):
    conn = sqlite3.connect('baza.db')
    cur = conn.cursor()
    cur.execute("SELECT vremia FROM trenirovki WHERE data=?", ((data),))
    result = cur.fetchall()
    result.sort()
    conn.commit()
    return result



def informacia_o_trenirovke(vremia, data):


    if data[0] == '0':
        data = data[1:]

    conn = sqlite3.connect('baza.db')
    cur = conn.cursor()
    cur.execute("SELECT nomer, adres, zena, min_chelovek, max_chelovek FROM trenirovki WHERE data=? and vremia=?", (data, vremia))
    result = cur.fetchone()
    conn.commit()

    rez = []
    if result != None:
        for a in result:
            rez.append(a)

        nomer = result[0]
        conn = sqlite3.connect('baza.db')
        cur = conn.cursor()
        cur.execute("SELECT telegram_id FROM zapis_na_trenirovky WHERE nomer_trenirovki=? ", (nomer, ))
        zapisalos = cur.fetchall()
        conn.commit()
        if zapisalos == []:
            klientov = 0
        else:
            klientov = len(zapisalos)
        rez.append(klientov)



    return rez

def redaktirovanie_trenirovki(nomer, stolbec, znachenie):

    conn = sqlite3.connect('baza.db')
    cur = conn.cursor()
    #формируем запрос
    sel = "UPDATE trenirovki SET " + stolbec + '=? WHERE nomer=? '
    cur.execute(sel, (znachenie, nomer))
    conn.commit()

def user_zapis_otmena_trenirovki(user, vremia, data):

    info = informacia_o_trenirovke(vremia, data)

    result = []

    if info != []:
        conn = sqlite3.connect('baza.db')
        cur = conn.cursor()

        cur.execute("SELECT nomer_pozicii FROM zapis_na_trenirovky WHERE nomer_trenirovki=? and telegram_id=?", (info[0], user))
        result = cur.fetchall()
        conn.commit()


        if (result == []) and (zapisyvaem_ili_net(data, vremia)):
            conn = sqlite3.connect('baza.db')
            cur = conn.cursor()
            trenirovka = (info[0], user)
            cur.execute(
                "INSERT INTO zapis_na_trenirovky (nomer_trenirovki, telegram_id) VALUES(?, ?);", trenirovka)
            conn.commit()

        else:
            conn = sqlite3.connect('baza.db')
            cur = conn.cursor()
            cur.execute("DELETE FROM zapis_na_trenirovky WHERE nomer_trenirovki=? and telegram_id=?", (info[0], user))
            conn.commit()

    return zapisyvaem_ili_net(data, vremia)

#Возвращает номера, даты, времена тренировок, на которые записался юзер
def user_zapisalsya_na_trenirovki(user):
    conn = sqlite3.connect('baza.db')
    cur = conn.cursor()
    cur.execute("SELECT nomer_trenirovki FROM zapis_na_trenirovky WHERE telegram_id=? ORDER BY nomer_pozicii", ((user),))
    result = cur.fetchall()

    conn.commit()
    trenirovka = []
    if result!= []:
        for tren in result:
            tren = tren[0]

            conn = sqlite3.connect('baza.db')
            cur = conn.cursor()
            cur.execute("SELECT data, vremia FROM trenirovki WHERE nomer=?", (tren, ))
            res_data_vremia = cur.fetchone()
            conn.commit()
            try:
                trenirovka.append((tren, nolik(res_data_vremia[0]), res_data_vremia[1]),)
            except:
                print('163 Тренировка отсутствует')

    return trenirovka

def zapisalis_na_trenirovky(nomer):
    conn = sqlite3.connect('baza.db')
    cur = conn.cursor()
    cur.execute("SELECT telegram_id FROM zapis_na_trenirovky WHERE nomer_trenirovki=?", (nomer,))
    res_telegram_id = cur.fetchall()
    conn.commit()

    result = []
    for user in res_telegram_id:
        conn = sqlite3.connect('baza.db')
        cur = conn.cursor()
        cur.execute("SELECT name, foto_id, telegram_id FROM klienty WHERE telegram_id=?", user)
        name_foto_id = cur.fetchone()
        conn.commit()

        result.append(name_foto_id)
    return result


def data_vremia_trenirovki_po_nomery(nomer_trenirovki):
    conn = sqlite3.connect('baza.db')
    cur = conn.cursor()
    cur.execute("SELECT data, vremia FROM trenirovki WHERE nomer=?", (nomer_trenirovki,))
    result = cur.fetchall()
    conn.commit()
    return result[0]

def zapisyvaem_ili_net(data, vremia):
    conn = sqlite3.connect('baza.db')
    cur = conn.cursor()
    cur.execute("SELECT nomer, max_chelovek FROM trenirovki WHERE data=? and vremia=?", (data, vremia))
    res_nomer = cur.fetchone()
    conn.commit()

    conn = sqlite3.connect('baza.db')
    cur = conn.cursor()
    cur.execute("SELECT telegram_id FROM zapis_na_trenirovky WHERE nomer_trenirovki=?", (res_nomer[0],))
    res_telegram_id = cur.fetchall()
    conn.commit()

    kolichestvo = len(res_telegram_id)

    if kolichestvo >= res_nomer[1]:
        zapis = False
    else:
        zapis = True
    return zapis

def vnesenie_v_bazy_id_knopok(user, mes_id_to_edit):
    conn = sqlite3.connect('baza.db')
    cur = conn.cursor()
    cur.execute("UPDATE klienty SET mes_id_to_edit=? WHERE telegram_id=? ", (mes_id_to_edit, user))
    conn.commit()

def id_knopok_dlya_redaktirovaniya(user):
    conn = sqlite3.connect('baza.db')
    cur = conn.cursor()
    cur.execute("SELECT mes_id_to_edit FROM klienty WHERE telegram_id=?", (user,))
    mes_id_to_edit = cur.fetchone()
    conn.commit()
    return mes_id_to_edit[0]

def mes_to_del_zapis(user, mes_id):
    conn = sqlite3.connect('baza.db')
    cur = conn.cursor()
    mes = (user, mes_id)
    cur.execute("INSERT INTO soobscheniya_chistki(id_telegram, id_soobscheniya) VALUES(?, ?);", mes)
    conn.commit()

def mes_to_del_info(user, mes_id):
    conn = sqlite3.connect('baza.db')
    cur = conn.cursor()
    mes = (user, mes_id)
    cur.execute("INSERT INTO soobscheniya_info(id_telegram, id_soobscheniya) VALUES(?, ?);", mes)
    conn.commit()

def den_nedeli(data, user):
    print(data)
    data = str(data)
    now = datetime.now()
    year = int(now.strftime("%y"))
    chislo_mesuaca = int(data[0:2])
    mesyac = int(data[3:5])
    data = datetime(year, mesyac, chislo_mesuaca)
    i = int(data.weekday())
    return fraza(i+24, user)

def data_plus_(data, n):

    data = str(data)
    now = datetime.now()
    year = int(now.strftime("%y"))
    chislo_mesuaca = int(data[0:2])
    mesyac = int(data[3:5])
    data = datetime(year, mesyac, chislo_mesuaca)
    data = data + timedelta(n)
    data = data.strftime("%d.%m")

    return data
