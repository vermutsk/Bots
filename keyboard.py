from aiogram import Bot, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


butt_fname =  KeyboardButton('Фамилия')
butt_name = KeyboardButton('Имя')
butt_oname = KeyboardButton('Отчество')
butt_dolj = KeyboardButton('Должность')
butt_room = KeyboardButton('Кабинет')
butt_phone = KeyboardButton('Телефон')
butt_mail =  KeyboardButton('Email')
butt_full = KeyboardButton('Полная')
butt_fio = KeyboardButton('Фио')
butt_new = KeyboardButton('Создать')
butt_change = KeyboardButton('Изменить')
butt_delete = KeyboardButton('Удалить')
butt_save = KeyboardButton('Сохранить')
board_1 = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).row(butt_full, butt_fio)
board_3 = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).row(butt_new, butt_change, butt_delete).add(butt_save)
board_2 = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).row(butt_dolj).row(butt_fname, butt_name, butt_oname).row(butt_room, butt_phone, butt_mail)