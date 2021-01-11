import requests
from config import TOKEN


def set_weebhook():
    res=requests.get(
        f'https://api.telegram.org/bot{TOKEN}/setWebhook',
        params={
                'url':'https://89.223.95.82:443/KB_8118_Bot'},
        files={'certificate':open('webhook_cert.pem','rb')}).json()