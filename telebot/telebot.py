from os import getenv
from datetime import datetime, timedelta
from pydantic.tools import parse_obj_as
import requests
from fastapi import APIRouter, Depends, HTTPException, Request, status
from typing import List, Optional
from sqlalchemy.orm import Session
from . import crud, schemas, models

router = APIRouter(
    prefix="/telebot",
    tags=["telebot"]
)

def get_db(request: Request):
    db = request.app.state.session()
    try:
        yield db
    finally:
        db.close()

@router.get("/categories")
def get_categories(db: Session = Depends(get_db)):
    return crud.get_categories(db)

@router.get("/letters/{patt}")
def get_letters(patt: str, db: Session = Depends(get_db)):
    return crud.get_by_letters(db, patt)

@router.get("/category/{cat}")
def get_category(cat: str, dt: Optional[datetime] = None, db: Session = Depends(get_db)):
    if dt == None: dt = datetime.now()
    return crud.get_by_cat(db, cat, dt)

@router.get("/programme/{prm}")
def get_programme(prm: str, dt: Optional[datetime] = None, db: Session = Depends(get_db)):
    if dt == None: dt = datetime.now()
    return crud.get_programme(db, prm, dt)

def start(res: schemas.tgrmResponse):
    res.text = """
Доступные команды.
/category - Выберите категорию передач
/timezone - Выберите вашу временную зону, чтобы бот правильно показывал время передач
/search - Поиск канала по буквам
"""

def search(res: schemas.tgrmResponse):
    res.text = 'Наберите фрагмент названия.\n'

def proccessList(lst: List, ch: str, res: schemas.tgrmResponse):
    telebot = getenv('TELEBOT')
    url = f'https://api.telegram.org/bot{telebot}/sendMessage'
    text, row = '', []
    for i, l in enumerate(lst):
        if i != 0 and i % 8 == 0:
            res.text, res.reply_markup = text, schemas.tgrmInlineKeyboardMarkup(inline_keyboard=[row])
            r = requests.post(url, data=res.json(exclude={'method'}, exclude_none=True), headers={'Content-Type': 'application/json'})
            #print(r.status_code, r.json())
            text, row = '', []
        text += f'{i+1}. {l[0]}\n' if l[0] is not None else f'{i+1}. Пусто\n'
        button = schemas.tgrmInlineKeyboardButton(text=str(i+1), callback_data = ch + (l[0] if l[0] is not None else 'Пусто'))
        row.append(button)
    res.text, res.reply_markup = text, schemas.tgrmInlineKeyboardMarkup(inline_keyboard=[row])


def proccessProg(prog: models.Programme, res: schemas.tgrmResponse, chc: str):
    if prog:
        desc = prog.pdesc if prog.pdesc else 'Содержание отсутствует' 
        res.parse_mode = 'HTML' 
        res.text = f'<b>{chc}</b>\n<i>{prog.pstart.strftime("%H:%M")} - {prog.pstop.strftime("%H:%M")}</i>\n<b><i>{prog.title}</i></b>\n{desc}\n'
        row = [schemas.tgrmInlineKeyboardButton(text='<<', callback_data=f'<{chc};{prog.pstart}'),
                schemas.tgrmInlineKeyboardButton(text='==', callback_data=f'{chc}'),
                schemas.tgrmInlineKeyboardButton(text='>>', callback_data=f'>{chc};{prog.pstop}')]
        res.reply_markup = schemas.tgrmInlineKeyboardMarkup(inline_keyboard=[row])
        print(res.reply_markup)
    else: res.text += """
************************************
К сожалению,
программа прередач отсутствует.
************************************
"""

def callback(db: Session, res: schemas.tgrmResponse, chc: str, dt: Optional[datetime] = None):
    if dt == None: dt = datetime.now()
    if chc[0] == '$':
        proccessList(lst = crud.get_by_cat(db, chc[1:], dt), ch = '', res=res)
    else:
        #print(chc)
        if chc[0] == '<' or chc[0] == '>':
            p = chc.find(';')
            dt = datetime.strptime(chc[p+1:],'%Y-%m-%d %H:%M:%S')
            dt =  dt + timedelta(minutes=1) if chc[0] == '>' else dt - timedelta(minutes=1)
            chc = chc[1:p]
        proccessProg(prog = crud.get_programme(db, chc, dt), res =res, chc=chc)

@router.post("/", response_model=schemas.tgrmResponse, response_model_exclude_none=True, status_code=status.HTTP_200_OK)
def telebot(update: schemas.tgrmUpdate, db: Session = Depends(get_db)):
    print(update)
    func_dict = {'/timezone': start, '/search': search, '/start': start, '/category': proccessList}
    if update.callback_query: 
        res = schemas.tgrmResponse(chat_id = update.callback_query.message.chat.id)
        callback(db=db, res=res, chc=update.callback_query.data)
    else: 
        res = schemas.tgrmResponse(chat_id = update.message.chat.id)
        if update.message.text in func_dict:
            func_args = {'/timezone': (res,), '/search': (res,), '/start': (res,), '/category': (crud.get_categories(db),'$',res)}
            func_dict[update.message.text](*func_args[update.message.text])
        else:
            proccessList(lst = crud.get_by_letters(db, update.message.text), ch = '', res=res)
    print(res)
    return res

