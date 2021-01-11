from pymongo import MongoClient
from config import MAIN_DB, ADMIN_DB
import requests
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from aiogram.types import ReplyKeyboardMarkup,KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

client = MongoClient("localhost", 27017) 
db = client['NEW_DB']
new_collection = db[MAIN_DB]
adm_collection = db[ADMIN_DB]

def parser():

    new_collection.remove({})
    adm_collection.remove({})

    list_url=list()
    string='https://www.dvfu.ru/'
    adrurl=string+"about/rectorate/scheme/"
    response=requests.get(adrurl ,headers={'User-Agent': UserAgent().chrome})
    html=response.content
    soup = BeautifulSoup(html,'html.parser')

    obj = soup.find('tr', attrs = {'class':'node-cells secondline'})
    obj = obj.find('td', attrs = {'class':'node-cell'})
    obj=obj.find('a')
    url=obj.attrs['href']
    list_url.append(url)

    obj = soup.find('td', attrs = {'class':'node-container'})
    obj=obj.findAll('a')
    for elem in obj:
        url=elem.attrs['href']
        list_url.append(url)

    list_of_posts=list()
    for url in list_url:

        document=dict()
        new_url=string+url
        response=requests.get(new_url ,headers={'User-Agent': UserAgent().chrome})
        html=response.content
        soup = BeautifulSoup(html,'html.parser')
        
        obj = soup.find( attrs = {'class':'row bigografy-block'})
        bigography=obj.find(attrs={'class':'col-md-8 col-sm-8 col-xs-12'})
        author_name=bigography.find('div',attrs={'class':'author-name h1'})
        if author_name!=None:
            author_name=author_name.text
            work=bigography.find(attrs = {'class':'author-dolj h3 mt-0 mb-4'})
            work=work.text
            adress=bigography.find(attrs = {'class':'block-address'})
            adress=adress.text
            phone=bigography.find(attrs = {'class':'block-phone'})
            phone=phone.text
            mail=bigography.find(attrs = {'class':'block-email'})
            mail=mail.text
        else:
            helper=obj.find(attrs={'class':'helpers-item'})
            author_name=helper.find('div',attrs={'class':'helpers-title'})
            author_name=author_name.text
            work=helper.find(attrs = {'class':'helpers-num'})
            work=work.text
            adress=helper.find('div',attrs = {'class':'block-address'})
            adress=adress.text
            phone=helper.find(attrs = {'class':'block-phone'})
            phone=phone.text
            mail=helper.find(attrs = {'class':'block-email'})
            mail=mail.text

        author_name=author_name.split()
        adress=adress.split(",")
        adress=adress[-1]

        document['doljname']=work
        document['Fname']=author_name[0]
        document['Name']=author_name[1]
        document['Oname']=author_name[2]
        document['Room']=adress
        document['Phone']=phone
        document['Mail']=mail
        list_of_posts.append(document)

    new_collection.insert_many(list_of_posts)
    adm_collection.insert_many(list_of_posts)
    list_of_posts.clear()

def save_adm(user_id, state):
    new_collection.remove({})
    docs = adm_collection.find({},{'_id' : 0,'edited': 0})
    full = []
    for doc in docs:
        if 'admin_id' in doc:
            if doc['admin_id'] == str(user_id):
                adm_collection.update_one({'doljname' : doc['doljname']}, {"$unset": {'admin_id' : 1}})
            doc.pop('admin_id')
        full.append(doc)
    new_collection.insert_many(full)
    

def db_list(js):
    many_doc = []
    one_doc = []
    for doc in js:
        one_doc = []
        for value in doc.values():
            one_doc.append(value)
        many_doc.append(one_doc)
    return many_doc

def num_list():
    js = adm_collection.find({}, {'doljname' : 1, '_id' : 0})
    full = db_list(js)
    g = 1
    full_text = ''
    for elem in full:
        for i in elem:
            full_text += f'{g}' + '. ' + i + '\n'
            g += 1
    return full_text

def create_reply_keyboard():
    lenght = adm_collection.find().count()
    if lenght >= 4:
        board_4 = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=4).insert(KeyboardButton('1'))
    else:
        board_4 = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).insert(KeyboardButton('1'))
    for i in range(2, lenght+1):
        board_4.insert(KeyboardButton(f'{i}'))
    return board_4