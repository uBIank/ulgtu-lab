import config # API ключ
import telebot # Telegram API
from telebot import types # под-библиотека для создания кнопок
import sys 
from datetime import datetime

import sqlite3

conn = sqlite3.connect('users_lb6-dn.db', check_same_thread=False)
cursor = conn.cursor() # Курсор для выполнения SQL_запросов

bot = telebot.TeleBot(config.apikey) # Инициализация бота

users = {} #Словарик с пользователями
results = [] #Набор данных - результаты запросов
start_val = 0 # Итератор

def default_message():
    def_text = """  
                Выберите команду:
                    /add - Добавить запись
                    /view - Посмотреть записи
                    /clear - Удалить пользователя
                """
    return def_text

@bot.message_handler(content_types=['text'])
def bot_start(message):
    
    global users
    global results
    try:
        if message.text == '/add': #Регистрация пользователя
            users.update({message.chat.id: {}})
            bot.send_message(message.from_user.id, "Укажи дату и время включения зеленого света на светофоре "
                                                   "ФОРМАТА (YYYY.MM.DD.HH.MM.SS)")
            bot.register_next_step_handler(message, bot_get_date_time_start)

        elif message.text == '/view': #Просмотр пользователей
            cursor.execute(
                """
                SELECT id as Номер,
                    date_start as Время_как_загорелся_зеленый,
                    date_end as Время_как_погас_зеленый,
                    count_car as Количество_машин_который_успели_проехать_на_зеленый,
                    count_car_stop as Количество_машин_который_ждут_в_очереди
                    FROM TrafficLights
                """
            )
            results = cursor.fetchall()
            check_start(start_val, results, message)



        elif message.text == '/clear':  # Удаление пользователя
            bot.send_message(message.from_user.id, "Для удаления, нужно ввести праоль доступа")
            bot.register_next_step_handler(message, bot_pass)


        elif message.text == '/YES':
            bot.send_message(message.from_user.id, "Укажите ID Записи")
            bot.register_next_step_handler(message, dostup_id)
            dostup = False


        else:
            bot.send_message(message.from_user.id, default_message())

    except Exception:
        print(sys.exc_info())

def bot_pass(message):

    global dostup
    global results

    if message.text == 'pass123456': # По-хорошему бы проверять id пользователя из белого листа
        dostup = True
        cursor.execute(
            """
            SELECT id as Номер,
                    date_start as Время_как_загорелся_зеленый,
                    date_end as Время_как_погас_зеленый,
                    count_car as Количество_машин_который_успели_проехать_на_зеленый,
                    count_car_stop as Количество_машин_который_ждут_в_очереди
                    FROM TrafficLights              
            """
        )
        results = cursor.fetchall()
        check_dostup(start_val, results, message)
    else:
        bot.send_message(message.from_user.id, "Пароль не правильный")
        bot.send_message(message.from_user.id, default_message())


def check_dostup(start_value, value_bd, mess):

    global start_val

    sms = ''
    for val in range(start_value, start_value + 10):
        if val < len(value_bd):
            sms += str(value_bd[val]) + '\n'
        else:
            break

    if sms != '':
        bot.send_message(mess.from_user.id, sms)

        keyboard = types.InlineKeyboardMarkup()
        key_check_yes = types.InlineKeyboardButton(text='Да', callback_data='dostup_Yes')
        keyboard.add(key_check_yes)

        key_check_no = types.InlineKeyboardButton(text='Нет', callback_data='dostup_No')
        keyboard.add(key_check_no)

        guestion = 'Выгрузить еще?'


    if val+1 < len(value_bd):

        bot.send_message(mess.from_user.id, text=guestion, reply_markup=keyboard)
    else:
        bot.send_message(mess.from_user.id, 'Удаляем? /YES /NO')

        start_val = 0
        dostup = True

    return

def dostup_id(message):

    cursor.execute(
        """
        Delete FROM TrafficLights
         where id == :id 
        """,
        {
        "id": message.text}
                   )

    if (cursor.rowcount != 0):
        conn.commit() # Подтверждение изменений
        bot.send_message(message.from_user.id, 'Данные с указанными ID были успешно удалены')

    else:
        bot.send_message(message.from_user.id, 'Ничего не было удалено')

    bot.send_message(message.from_user.id, default_message())

def bot_get_date_time_start(message):
    global users
    try:

        users[message.chat.id].update({'date_start': datetime.strptime(message.text, '%Y.%m.%d.%H.%M.%S')})
        bot.send_message(message.from_user.id, "Укажи дату и время выключения зеленого света на светофоре "
                                               "ФОРМАТА (YYYY.MM.DD.HH.MM.SS)")
        bot.register_next_step_handler(message, bot_get_date_time_end)

    except Exception:
        print(sys.exc_info())
        bot.send_message(message.from_user.id, "Укажи дату и время включения зеленого света на светофоре "
                                               "ФОРМАТА (YYYY.MM.DD.HH.MM.SS)")
        bot.register_next_step_handler(message, bot_get_date_time_start)


def bot_get_date_time_end(message):
    global users
    try:

        users[message.chat.id].update({'date_end': datetime.strptime(message.text, '%Y.%m.%d.%H.%M.%S')})
        bot.send_message(message.from_user.id, "Укажи количество машин которые успели проехать на зеленый")
        bot.register_next_step_handler(message, bot_get_count_car)

    except Exception:
        print(sys.exc_info())
        bot.send_message(message.from_user.id, "Укажи дату и время выключения зеленого света на светофоре"
                                               "ФОРМАТА (YYYY.MM.DD.HH.MM.SS)")
        bot.register_next_step_handler(message, bot_get_date_time_end)


def bot_get_count_car(message):
    global users
    try:

        users[message.chat.id].update({'count_car': int(message.text)})
        bot.send_message(message.from_user.id, "Укажи количество автомобилей в ожидании ")
        bot.register_next_step_handler(message, bot_get_count_car_stop)

    except Exception:
        print(sys.exc_info())
        bot.send_message(message.from_user.id, "Укажи количество машин которые успели проехать на зеленый")
        bot.register_next_step_handler(message, bot_get_count_car)

def bot_get_count_car_stop(message):

    global users
    try:

        users[message.chat.id].update({'count_car_stop': int(message.text)})

        keyboard = types.InlineKeyboardMarkup()
        key_yes = types.InlineKeyboardButton(text='Добавить данные в базу?', callback_data='Yes')
        keyboard.add(key_yes)

        key_no = types.InlineKeyboardButton(text='Отменить добавление данных в базу?', callback_data='No')
        keyboard.add(key_no)

        guestion = ('Добавить данные в базу?\n '
                    'Зеленый загорелся в {}\n Зеленый погас в {}\n '
                    'Количество машин успевших проехать на зеленый: {}\n'
                    'Количество машин в ожидании {}').format(
            str(users[message.chat.id]['date_start']),
            str(users[message.chat.id]['date_end']), users[message.chat.id]['count_car'], users[message.chat.id]['count_car_stop'])

        bot.send_message(message.from_user.id, text=guestion, reply_markup=keyboard)

    except Exception:
        print(sys.exc_info())
        bot.send_message(message.from_user.id, ", Укажи количество автомобилей в ожидании ")
        bot.register_next_step_handler(message, bot_get_count_car_stop)


def check_start(start_value, value_bd, mess):

    global start_val

    try:
        num = 1
        sms = 'id_table, start_green, stop_green, car_drive, car_stop\n'
        for val in range(start_value, start_value+10):
            if val < len(value_bd):
                sms += str(start_value+num) + str(value_bd[val][1:]) + '\n'
                num += 1
            else:
                break


        if sms != '':
            bot.send_message(mess.from_user.id, sms)

            keyboard = types.InlineKeyboardMarkup()
            key_check_yes = types.InlineKeyboardButton(text='Выгрузить еще', callback_data='ch_Yes')
            keyboard.add(key_check_yes)

            key_check_no = types.InlineKeyboardButton(text='Больше не выгружать', callback_data='ch_No')
            keyboard.add(key_check_no)


            guestion = 'Выгрузить еще?'

        if val+1 < len(value_bd):
            bot.send_message(mess.from_user.id, text=guestion, reply_markup=keyboard)
        else:
            bot.send_message(mess.from_user.id, 'Увы, но список подошел к концу')
            start_val = 0
            bot.send_message(mess.from_user.id, default_message())
        return

    except Exception:
        print(sys.exc_info())


@bot.callback_query_handler(func=lambda call:True)
def callback_worker(call):

    try:
        global users
        global results
        global start_val
        if call.data == 'Yes':
            cursor.execute(""" 
                        WITH TempBD AS (
                                SELECT MIN(id) AS id FROM TrafficLights
                                UNION ALL
                                SELECT id + 1 FROM TempBD WHERE id < (SELECT MAX(id) FROM TrafficLights)
                        )
                                SELECT CASE WHEN MIN(TempBD.id) IS NULL
                                    THEN (SELECT MAX(id) FROM TrafficLights) + 1
                                    ELSE MIN(TempBD.id)
                                    END
                                FROM TempBD
                            LEFT JOIN TrafficLights ON TrafficLights.id = TempBD.id
                                where TrafficLights.id IS NULL
                        """
                           ) # Запрос для поиска пустых строк в таблице
            res = cursor.fetchall()[0][0] # Возврат первого значения из первого ряда кортежем
            print(res)

            cursor.execute("""
                INSERT INTO TrafficLights (id, date_start, date_end, count_car, count_car_stop)
                 values(:id, :date_start, :date_end, :count_car, :count_car_stop)
                """, {
                        "id": res, # Ранее найденая пустая строка
                        "date_start" :  users[call.from_user.id]['date_start'],
                        "date_end" :  users[call.from_user.id]['date_end'],
                        "count_car" :  str(users[call.from_user.id]['count_car']),
                        "count_car_stop" :  users[call.from_user.id]['count_car_stop']})

            conn.commit() # Подтверждение изменений
            bot.send_message(call.from_user.id, 'Данные были успешно добавлены')
            bot.send_message(call.from_user.id, default_message())

        elif call.data == 'No':
            bot.send_message(call.message.chat.id, 'Данные не были добавлены!')
            bot.send_message(call.from_user.id, default_message())

        elif call.data == 'ch_Yes':
            start_val += 10
            check_start(start_val, results, call,)

        elif call.data == 'ch_No':
            start_val = 0
            bot.send_message(call.message.chat.id, default_message())

        elif call.data == 'dostup_Yes':
            start_val += 10
            check_dostup(start_val, results, call)

        elif call.data == 'dostup_No':
            start_val = 0
            bot.send_message(call.message.chat.id, 'Удаляем? /YES /NO')


        elif call.data == 'no_delete':
            bot.send_message(call.message.chat.id, default_message())



    except Exception:
        print(sys.exc_info())



bot.enable_save_next_step_handlers(delay=2) # Пошаговый запрос данных
bot.load_next_step_handlers()
bot.polling(none_stop=True) # Работа бота нон-стоп