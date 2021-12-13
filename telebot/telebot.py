from os import getenv
from datetime import datetime, timedelta
from time import timezone
import requests
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from typing import List, Optional, Union
from sqlalchemy.orm import Session

from . import crud
from dependencies import get_db
import models, schemas
import json

router = APIRouter(
    prefix="/telebot",
    tags=["telebot"]
)

@router.get("/categories")
def get_categories(db: Session = Depends(get_db)):
    return crud.get_categories(db)

@router.get("/letters/{patt}")
def get_letters(patt: str, db: Session = Depends(get_db)):
    return crud.get_by_letters(db, patt)

@router.get("/category/{cat}")
def get_category(cat: str, dt: Optional[datetime] = datetime.utcnow(), db: Session = Depends(get_db)):
    return crud.get_by_cat(db, cat, dt)

@router.get("/programme/{prm}")
def get_programme(prm: str, dt: Optional[datetime] = datetime.utcnow(), db: Session = Depends(get_db)):
    return crud.get_programme(db, prm, dt)

def get_timezones():
    return [('<b>МСК-1</b> - Калининград',), ('<b>МСК</b> - Москва, Казань, Сочи',), ('<b>МСК+1</b> - Самара, Волгоград',), 
            ('<b>МСК+2</b> - Уфа, Екатеринбург, Тюмень',), ('<b>МСК+3</b> - Омск',), ('<b>МСК+4</b> - Красноярск, Томск, Барнаул',),
            ('<b>МСК+5</b> - Иркутск, Улан-Удэ',), ('<b>МСК+6</b> - Чита, Якутск',), ('<b>МСК+7</b> - Владивосток, Хабаровск',)]

def get_tz_string(shift: int):
    #print(shift)
    ind = shift//60
    timezones = get_timezones()
    return f'Ваш часовой пояс:\n{timezones[ind-2][0]}' if ind-2 in range(len(timezones)) else f'UTC + {ind}'
            

def start(res: schemas.tgrmSendMessage):
    res.text = """
Доступные команды.
/category - Выберите категорию передач
/search - Поиск канала по буквам
/timezone - Выберите вашу временную зону, чтобы бот правильно показывал время передач
/location - Определение временной зоны по Вашему местоположению
"""

def search(res: schemas.tgrmSendMessage):
    res.text = 'Наберите фрагмент названия.\n'

def location(res: schemas.tgrmSendMessage):
    button = schemas.tgrmKeyboardButton(text='Послать местоположение',request_location=True)
    res.text = 'Нажмите кнопку "Послать местоположение"'
    res.reply_markup = schemas.tgrmReplyKeyboardMarkup(tag='Reply', keyboard=[[button]], resize_keyboard=True, one_time_keyboard=True)

def proccessList(lst: List, ch: str, res: schemas.tgrmSendMessage):
    telebot = getenv('TELEBOT')
    url = f'https://api.telegram.org/bot{telebot}/sendMessage'
    text, row = '', []
    for i, l in enumerate(lst):
        if i != 0 and i % 8 == 0:
            res.text, res.reply_markup = text, schemas.tgrmInlineKeyboardMarkup(tag='Inline', inline_keyboard=[row])
            #print(res.json())
            r = requests.post(url, data=res.json(exclude_none=True), headers={'Content-Type': 'application/json'})
            #print(r.status_code)
            text, row = '', []
        text += f'{i+1}. {l[0]}\n' if l[0] is not None else f'{i+1}. Пусто\n'
        callback_data = str(i+1) if ch == '#' else (l[0] if l[0] is not None else 'Пусто')
        button = schemas.tgrmInlineKeyboardButton(text=str(i+1), callback_data = ch + callback_data)
        row.append(button)
    res.text, res.reply_markup = text, schemas.tgrmInlineKeyboardMarkup(tag='Inline', inline_keyboard=[row])


def proccessProg(prog: models.Programme, res: schemas.tgrmSendMessage, chc: str, shift: Optional[int] = 180):
    if prog:
        desc = prog.pdesc if prog.pdesc else 'Содержание отсутствует'
        start = prog.pstart + timedelta(minutes=shift)
        stop = prog.pstop + timedelta(minutes=shift)  
        res.parse_mode = 'HTML' 
        res.text = f'<b>{chc}</b>\n<i>{start.strftime("%H:%M")} - {stop.strftime("%H:%M")}</i>\n<b><i>{prog.title}</i></b>\n{desc}\n'
        row = [schemas.tgrmInlineKeyboardButton(text='<<', callback_data=f'<{chc};{prog.pstart}'),
                schemas.tgrmInlineKeyboardButton(text='==', callback_data=f'{chc}'),
                schemas.tgrmInlineKeyboardButton(text='>>', callback_data=f'>{chc};{prog.pstop}')]
        res.reply_markup = schemas.tgrmInlineKeyboardMarkup(tag='Inline', inline_keyboard=[row])
        #print(res.reply_markup)
    else: res.text += """
************************************
К сожалению,
программа прередач отсутствует.
************************************
"""

def proccessTimezone(update: schemas.tgrmUpdate, res: schemas.tgrmSendMessage):
    #timezones = get_timezones()
    if update.callback_query:
        user = update.callback_query.from_
        tz = int(update.callback_query.data[1:])+1
        final = get_tz_string(tz*60)
    elif update.message.location:
        user = update.message.from_
        name = getenv('GEONAME')
        r = requests.get(f'http://api.geonames.org/timezoneJSON?lat={update.message.location.latitude}\
            &lng={update.message.location.longitude}&username={name}')
        if r.status_code != 200:
            tz = None 
            final = r.json()
        else:
            tz = int(r.json()["rawOffset"])
            final = get_tz_string(tz*60)
    res.text = f'Здравствуйте, <i>{user.first_name}'
    if user.last_name: res.text += f' {user.last_name}'
    res.text += f'.</i>\n' + final
    res.parse_mode = 'HTML'
    if tz != None:
        res.reply_markup = schemas.tgrmInlineKeyboardMarkup(tag='Inline',inline_keyboard=[[schemas.tgrmInlineKeyboardButton(text='Сохранить', callback_data = f'@{user.first_name};{str(60*tz)}'),
                            schemas.tgrmInlineKeyboardButton(text='Не сохранять', callback_data = '@')]])

def callback(db: Session, res: schemas.tgrmSendMessage, chc: str, dt: Optional[datetime] = datetime.utcnow()):
    if chc[0] == '$':
        proccessList(lst = crud.get_by_cat(db, chc[1:], dt), ch = '', res=res)
    elif chc[0] == '@':
        if len(chc) > 1:
            first_name, shift = chc.split(';')
            #print(first_name,shift)
            crud.update_telebot_user(db=db,chat_id=res.chat_id,first_name=first_name[1:],shift=int(shift))
            res.text = f'{first_name[1:]}, Ваш часовой пояс сохранён.\n' + get_tz_string(int(shift))
            res.parse_mode = 'HTML'
        else:
            telebot_user = crud.get_telebot_user(db=db, chat_id=res.chat_id)
            if telebot_user:
                res.text = f'{telebot_user.first_name}, ' + get_tz_string(telebot_user.shift)
                res.parse_mode = 'HTML'
            else: res.text = 'Ваш часовой пояс по умолчанию - Москва'
    else:
        #print(chc)
        if chc[0] == '<' or chc[0] == '>':
            p = chc.find(';')
            dt = datetime.strptime(chc[p+1:],'%Y-%m-%d %H:%M:%S')
            dt =  dt + timedelta(minutes=1) if chc[0] == '>' else dt - timedelta(minutes=1)
            chc = chc[1:p]
        r = crud.get_telebot_user(db=db,chat_id=res.chat_id)
        if r: proccessProg(prog = crud.get_programme(db, chc, dt), res =res, chc=chc, shift=r.shift)
        else: proccessProg(prog = crud.get_programme(db, chc, dt), res =res, chc=chc)

@router.post("/", response_model=Optional[schemas.tgrmSendMessage], response_model_exclude_none=True, status_code=status.HTTP_200_OK)
async def telebot(update: schemas.tgrmUpdate, request: Request, response: Response, db: Session = Depends(get_db)):
    req = await request.json()
    #print(json.dumps(req, indent=2, sort_keys=False))
    func_dict = {'/timezone': proccessList, '/search': search, '/start': start, '/location': location, '/category': proccessList}
    if update.callback_query: 
        res = schemas.tgrmSendMessage(chat_id = update.callback_query.message.chat.id, text='')
        if update.callback_query.data[0] == '#': proccessTimezone(update=update, res=res)
        else: callback(db=db, res=res, chc=update.callback_query.data)
    elif update.message: 
        res = schemas.tgrmSendMessage(chat_id = update.message.chat.id, text='')
        if update.message.text in func_dict:
            func_args = {'/timezone': (get_timezones(),'#',res), '/search': (res,), '/start': (res,), '/location': (res,),
                '/category': (crud.get_categories(db),'$',res)}
            if update.message.text == '/timezone': res.parse_mode = 'HTML'
            func_dict[update.message.text](*func_args[update.message.text])
        elif update.message.location:
            proccessTimezone(update=update,res=res)
        else:
            proccessList(lst = crud.get_by_letters(db, update.message.text), ch = '', res=res)
    else:
        res = None
    #response.headers['Content-Type'] = 'application/json; charset=UTF-8'
    if res: res.method = 'sendMessage'
    #print(res.json(exclude_none=True, indent=2, ensure_ascii=False))
    return res

