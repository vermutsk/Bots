from aiogram import Bot, types
from pymongo import MongoClient
from aiogram.utils import executor
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.utils.helper import Helper, HelperMode, Item
from aiogram.contrib.fsm_storage.mongo import MongoStorage
from aiogram.utils.markdown import text, bold, code
from aiogram.types import ParseMode, ReplyKeyboardRemove
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.routing import Route
from starlette.responses import JSONResponse
from starlette.middleware import Middleware

from weebhook import set_weebhook
from keyboard import board_1, board_2, board_3
from functions import parser, db_list, num_list, create_reply_keyboard, save_adm
from config import TOKEN, MAIN_DB, ADMIN_DB

client = MongoClient("localhost", 27017) 
db = client['NEW_DB']
new_collection = db[MAIN_DB]
adm_collection = db[ADMIN_DB]

bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MongoStorage())

class States(Helper):
    mode = HelperMode.snake_case
    ADMIN = Item()
    DELETE = Item()
    FIO = Item()
    DOLJ = Item()
    ADRESS = Item()
    EMAIL = Item()
    PHONE = Item()
    CHANGE = Item()
    CHANGE_ROOM = Item()

async def home(request: Request):
    if request.json()['message'][0].type ==types.Message:
        message_handler(request)

@dp.message_handler(commands=['start'], state = '*')
async def process_start_command(msg: types.Message, state: FSMContext):
    await bot.send_message(msg.chat.id, 'Добрейший вечерочек!\nПиши /help, '
                        'чтобы узнать список доступных команд!')

@dp.message_handler(commands=['help'], state = '*')
async def process_help_command(msg: types.Message, state: FSMContext):
    mess = text(bold('Смотри, я могу ответить за следующее:'),
                '/info - выведет список', '/worker - поиск по должности', 
                '/edit - внесение изменений', sep = "\n")
    await bot.send_message(msg.chat.id, mess, parse_mode=ParseMode.MARKDOWN)

@dp.message_handler(commands=['edit'], state = '*')
async def admin_command(msg: types.Message, state: FSMContext):
    user_id = msg.from_user.id
    acsess = await bot.get_chat_member(msg.chat.id, user_id)
    if acsess['status'] == 'administrator' or acsess['status'] == 'creator':
        await state.set_state(States.ADMIN)
        #t = Timer(600, save_adm(user_id))
        #t.start()
        await bot.send_message(msg.chat.id, "Админь", reply_markup=board_3)
        return
    else:
        await bot.send_message(msg.chat.id, "Ошибка доступа. Вы не являетесь админом.") 
        return

@dp.message_handler(commands=['info'], state = '*')
async def list_command(msg: types.Message, state: FSMContext):
    await bot.send_message(msg.chat.id, "Как много информации тебе нужно?", reply_markup=board_1)
    #клав 'полная - фио'

@dp.message_handler(commands=['worker'], state = '*')
async def process_worker_command(msg: types.Message, state: FSMContext):
    board_4 = create_reply_keyboard()
    full_text = num_list()
    await bot.send_message(msg.chat.id, full_text)
    await bot.send_message(msg.chat.id, "Вот все руководство, выбирай", reply_markup=board_4)
    #выводит клав с нумерован должностями

@dp.message_handler(state=States.ADMIN, content_types=['text']) #режим админа: ADMIN
async def admin(msg: types.Message, state: FSMContext):
    text = msg.text
    user_id = msg.from_user.id
    dolj = ''
    if text == 'Создать': #создание нового документа: DOLJ, FIO, ADRESS, PHONE, EMAIL
        if dolj == '':
            await state.set_state(States.DOLJ)
            await bot.send_message(msg.chat.id, "Введи должность:" )
            return
    elif text == 'Изменить':#изменение существующего документа: CHANGE, CHANGE_ROOM
        board_4 = create_reply_keyboard()
        await state.set_state(States.CHANGE)
        full_text = num_list()
        await bot.send_message(msg.chat.id, full_text)
        await bot.send_message(msg.chat.id, "Это весь список, кого будем редактировать?", reply_markup=board_4)
    elif text == 'Удалить':#удаление документа из коллекции: DELETE
        board_4 = create_reply_keyboard()
        await state.set_state(States.DELETE)
        full_text = num_list()
        await bot.send_message(msg.chat.id, full_text)
        await bot.send_message(msg.chat.id, "Это весь список, кого будем удалять?", reply_markup=board_4)
    elif text == 'Сохранить': #обновление коллекции, сброс состояния
        save_adm(user_id)
        await state.finish()
        await bot.send_message(msg.chat.id, "Воистину админь")
    elif text == 'Запуск парсера':
        parser()
    else:
        await bot.send_message(msg.chat.id, "Сохраните изменения, внесенные в режиме админа")

@dp.message_handler(state=States.DOLJ, content_types=['text'])
async def dolj(msg: types.Message, state: FSMContext):
    dolj = msg.text                             #получаем текст из сообщения
    if dolj.isalpha(): 
        change = adm_collection.find({}, {'_id' : 0, 'edited': 0})
        full = db_list(change)
        for i in range(len(full)):
            if dolj in full[i]:
                await bot.send_message(msg.chat.id, 'Руководитель с такой должностью уже существует')
                return
        await state.set_state(States.ADMIN)     #смена состояния на админку
        await state.update_data(doljname=dolj)  #привязка текущей инфы к состоянию
        await state.set_state(States.FIO)       #смена состояния на следующее
        await bot.send_message(msg.chat.id, 'Введи фамилию, имя и отчество через пробелы')
    else:
        await bot.send_message(msg.chat.id, 'Неверный формат')

@dp.message_handler(state=States.FIO, content_types=['text'])
async def fio(msg: types.Message, state: FSMContext):
    fio = msg.text
    if fio.istitle():
        fio = fio.split(' ')
        if len(fio) != 3:
            await bot.send_message(msg.chat.id, 'Неверный формат!\nВведи фамилию, имя и отчество через пробелы')
            return
        await state.set_state(States.ADMIN)
        await state.update_data(Fname=fio[0])
        await state.update_data(Name=fio[1])
        await state.update_data(Oname=fio[2])
        await state.set_state(States.ADRESS)
        await bot.send_message(msg.chat.id, "Введи кабинет: ")
    else:
        await bot.send_message(msg.chat.id, 'Неверный формат')

@dp.message_handler(state=States.ADRESS, content_types=['text'])
async def adress(msg: types.Message, state: FSMContext):
    adress = str(msg.text)
    if adress.isalnum():
        await state.set_state(States.ADMIN)
        await state.update_data(Room=adress)
        await state.set_state(States.PHONE)
        await bot.send_message(msg.chat.id, "Введи телефон: ")
    else:
        await bot.send_message(msg.chat.id, 'Неверный формат')

@dp.message_handler(state=States.PHONE, content_types=['text'])
async def phone(msg: types.Message, state: FSMContext):
    phone = str(msg.text)
    if phone.isdigit() is False:
        await bot.send_message(msg.chat.id, 'Неверный формат')
    elif phone.count('+') == 0 and phone[1:].isdigit() is False:
        await bot.send_message(msg.chat.id, 'Неверный формат')
    else:
        await state.set_state(States.ADMIN)
        await state.update_data(Phone=phone)
        await state.set_state(States.EMAIL)
        await bot.send_message(msg.chat.id, "Введи email: ")

@dp.message_handler(state=States.EMAIL, content_types=['text'])
async def email(msg: types.Message, state: FSMContext):
    email = msg.text
    if email.count('@') == 1:
        email1 = email.split('@')
        if email1[0].isalnum() and email1[1].count('.')==1:
            email1 = email1[1].split('.')
            if email1[0].isalpha() and email1[1].isalpha():
                await state.set_state(States.ADMIN)
                await state.update_data(Mail=email)
                user_data = await state.get_data()  #получаем всю инфу из состояния
                user_data.update({'edited': '1'})
                results = []
                results.append(user_data)
                adm_collection.insert_many(results) #добавление документа в adm_collection
                await bot.send_message(msg.chat.id, "Если это все, что ты хотел - жми 'Сохранить', "
                                        "ну или выбирай, что будем делать", reply_markup=board_3)
            else:
                await bot.send_message(msg.chat.id, 'Неверный формат')
        else:
            await bot.send_message(msg.chat.id, 'Неверный формат')
    else:
        await bot.send_message(msg.chat.id, 'Неверный формат')

@dp.message_handler(state=States.CHANGE, content_types=['text']) #режим внесения изменений
async def change(msg: types.Message, state: FSMContext):
    text = msg.text
    board_4 = create_reply_keyboard()
    key_list = ['doljname', 'Fname', 'Name', 'Oname', 'Room', 'Phone', 'Mail'] 
    if  text.isdigit():             #получает номер выбранного руководителя
        code = int(text)-1
        change = adm_collection.find({}, {'_id' : 0, 'edited': 0}).skip(code).limit(1)
        full = db_list(change)
        user_id = msg.from_user.id
        if len(full) < 1:           #проверка на существования такого номера в коллекции
            full_text = num_list()
            await bot.send_message(msg.chat.id, full_text)
            await bot.send_message(msg.chat.id, "Выбери кого редактироать клавиатуре!", reply_markup=board_4)
            return
        elif 'admin_id' in full[0]:      #проверка admin_id, не допускает параллельного редактирования
            if full[0]['admin_id'] != str(user_id):
                await bot.send_message(msg.chat.id, 'Редактирование сейчас недоступно, выберите другого человека', reply_markup=board_4)
                return
        else:
            new_doc = {'admin_id' : f'{user_id}'}
            adm_collection.update_one({'doljname' : full[0][0]}, {"$set": new_doc})
        await state.update_data(code=text)
        full_text = ''
        for elem in full:
            if 'admin_id' in elem:
                elem.pop('admin_id')
            for value in elem:
                full_text += str(value) + '\n'
        await bot.send_message(msg.chat.id, full_text)
        await bot.send_message(msg.chat.id, "Что будем менять?", reply_markup=board_2)
    elif text == 'Назад':           #возврат в режим админа
        await state.set_state(States.ADMIN)
        await bot.send_message(msg.chat.id, "Если это все, что ты хотел - жми 'Сохранить', "
                            "ну или выбирай, что будем делать", reply_markup=board_3)
    else:                           #принимает параметр изменения и новые значения
        butt_list = ['Должность', 'Фамилия', 'Имя', 'Отчество', 'Кабинет', 'Телефон', 'Email']
        for i in range(len(butt_list)):
            if text == butt_list[i]:#запоминаем параметр изменения
                data = await state.get_data()
                if 'code' in data:
                    await state.update_data(text=i)
                    if i == 4:
                        await state.set_state(States.CHANGE_ROOM)
                    await bot.send_message(msg.chat.id, "Введи новое значение")
                    return
                else:
                    await bot.send_message(msg.chat.id, "Сначала выбери кого будем изменять", reply_markup=board_4)
        data = await state.get_data()
        if 'text' in data:          #проверка на параметр изменения&внесение изменений
            code = int(data['code'])    #номер руководителя в коллекции
            num = int(data['text'])     #параметр изменения
            change = adm_collection.find({}, {'_id' : 0, 'edited': 0}).skip(code-1).limit(1)
            full = db_list(change)
            new_doc = {f'{key_list[num]}' : text, 'edited': '1'}
            adm_collection.update_one({'doljname' : full[0][0]}, {"$set": new_doc})
            await state.set_state(States.ADMIN)
            await bot.send_message(msg.chat.id, "Если это все, что ты хотел - жми 'Сохранить', ну или выбирай, что будем делать", reply_markup=board_3)
        else:
            await bot.send_message(msg.chat.id, "Выбери, что будем менять на клавиатуре, либо напиши 'Назад', вернуться", reply_markup=board_2)

@dp.message_handler(state=States.CHANGE_ROOM, content_types=['text'])#режим редактирования кабинета
async def change_room(msg: types.Message, state: FSMContext):
    text = msg.text
    key_list = ['doljname', 'Fname', 'Name', 'Oname', 'Room', 'Phone', 'Mail']
    await state.set_state(States.CHANGE)
    data = await state.get_data()
    code = int(data['code'])
    num = int(data['text'])
    change = adm_collection.find({}, {'_id' : 0, 'edited': 0}).skip(code-1).limit(1)
    full = db_list(change)
    new_doc = {f'{key_list[num]}' : text, 'edited': '1'}
    adm_collection.update_one({'doljname' : full[0][0]}, {"$set": new_doc})
    await state.set_state(States.ADMIN)
    await bot.send_message(msg.chat.id, "Если это все, что ты хотел - жми 'Сохранить', ну или выбирай, что будем делать", reply_markup=board_3)

@dp.message_handler(state=States.DELETE, content_types=['text'])#режим удаления
async def delete(msg: types.Message, state: FSMContext):
    text = msg.text
    board_4 = create_reply_keyboard()
    if  text.isdigit():
        code = int(text)-1
        delete = adm_collection.find({}, {'_id' : 0, 'edited': 0}).skip(code).limit(1)
        full = db_list(delete)
        user_id = msg.from_user.id
        if len(full) < 1:           #проверка на существования такого номера в коллекции
            full_text = num_list()
            await bot.send_message(msg.chat.id, full_text)
            await bot.send_message(msg.chat.id, "Выбери кого удалить клавиатуре!", reply_markup=board_4)
            return
        elif len(full[0]) > 7:      #проверка admin_id
            if full[0][7] != str(user_id):
                await bot.send_message(msg.chat.id, 'Редактирование сейчас недоступно, выберите другого человека', reply_markup=board_4)
                return
        else:
            new_doc = {'admin_id' : f'{user_id}'}
            old_doc = {'doljname' : full[0][0], 'Fname':full[0][1], 'Name':full[0][2], 'Oname':full[0][3], 'Room':full[0][4], 'Phone':full[0][5], 'Mail':full[0][6]}
            adm_collection.update_one(old_doc, {"$set": new_doc})
        adm_collection.remove(old_doc)    #удаление документа
        await state.set_state(States.ADMIN)
        await bot.send_message(msg.chat.id, "Если это все, что ты хотел - жми 'Сохранить', ну или выбирай, что будем делать", reply_markup=board_3)

@dp.message_handler(content_types=['text'], state = '*')#вывод инфы по коммандам edit & worker
async def echo(msg: types.Message, state: FSMContext):
    text = msg.text
    if text == 'Полная':    #edit
        js = new_collection.find({}, { '_id' : 0, 'edited': 0})
        full = db_list(js)
        for elem in full:
            full_text = ''
            for i in elem:
                full_text += str(i) + '\n'
            await bot.send_message(msg.chat.id, full_text)
    elif text == 'Фио':     #edit
        js = new_collection.find({}, { 'Phone' : 0, 'Room' : 0, 'Mail': 0, '_id' : 0})
        full = db_list(js)
        for elem in full:
            full_text = []
            for i in elem:
                full_text.append(str(i))
            full_text.insert(1, '-')
            full_text = ' '.join(full_text)
            await bot.send_message(msg.chat.id, full_text)
    elif text.isdigit():    #worker
        js = new_collection.find({}, { '_id' : 0, 'edited': 0})
        full = db_list(js)
        code = int(text)-1
        full_text = ''
        for i in range(len(full)):
            if code == i:
                for g in full[i]:
                    full_text += str(g) + '\n'
                await bot.send_message(msg.chat.id, full_text)
    else:
        await bot.send_message(msg.chat.id, 'Я не знаю таких слов')

routes=[
    Route("/KB_8118_Bot", home, methods=['post'])]

middlewares=[
    Middleware(home)]


if __name__ == '__main__':
    parser()
    set_weebhook()
    app=Starlette(debug=False, routes=routes) #middleware=middlewares)
    executor.start_polling(dp)