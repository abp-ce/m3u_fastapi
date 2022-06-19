from datetime import datetime

from sqlalchemy.orm import Session

import models


def get_categories(db: Session):
    return db.query(models.Programme.cat).distinct().all()


def get_by_letters(db: Session, pat: str):
    return db.query(models.Channel.disp_name).filter(
        models.Channel.disp_name_l.like(f'%{pat.lower()}%')
    ).all()


def get_by_cat(db: Session, cat: str, tm: datetime):
    tcat = None if cat == 'Пусто' else cat
    return db.query(models.Channel.disp_name).join(models.Programme).filter(
        models.Programme.pstart <= tm,
        models.Programme.pstop > tm,
        models.Programme.cat == tcat
    ).all()


def get_by_id(db: Session, id: str):
    return db.query(models.Channel.disp_name).filter(
        models.Channel.ch_id == id
    ).first()


def get_programme(db: Session, prm: str, tm: datetime):
    return db.query(models.Programme).join(models.Channel).filter(
        models.Programme.pstart <= tm,
        models.Programme.pstop > tm,
        models.Channel.disp_name == prm
    ).first()


def get_telebot_user(db: Session, chat_id: int):
    return db.query(models.Telebot_User).filter(
        models.Telebot_User.chat_id == chat_id
    ).first()


def update_telebot_user(db: Session, chat_id: int,
                        first_name: str, shift: int):
    res = db.query(models.Telebot_User).filter(
        models.Telebot_User.chat_id == chat_id
    ).first()
    if res:
        res.first_name = first_name
        res.shift = shift
    else:
        res = models.Telebot_User(chat_id=chat_id, first_name=first_name,
                                  shift=shift)
    db.add(res)
    db.commit()
