from datetime import datetime
from datetime import datetime
from sqlalchemy.orm import Session

from . import models, schemas

def get_categories(db: Session):
    return db.query(models.Programme.cat).distinct().all()

def get_by_letters(db: Session, pat: str):
    return db.query(models.Channel.disp_name).filter(models.Channel.disp_name_l.like(f'%{pat.lower()}%')).all()

def get_by_cat(db: Session, cat: str, tm: datetime): 
    tcat = None if cat == 'Пусто' else cat
    return db.query(models.Channel.disp_name).join(models.Programme).filter(models.Programme.pstart <= tm, 
            models.Programme.pstop > tm, models.Programme.cat == tcat).all()

def get_by_id(db: Session, id: str):
    return db.query(models.Channel.disp_name).filter(models.Channel.ch_id == id).first()

def get_programme(db: Session, prm: str, tm: datetime):
    return db.query(models.Programme).join(models.Channel).filter(models.Programme.pstart < tm, models.Programme.pstop > tm, 
            models.Channel.disp_name == prm).first()
