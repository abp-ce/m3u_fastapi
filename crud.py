from datetime import datetime, timedelta

from sqlalchemy.orm import Session

import models
from schemas import UserFromForm


def user_by_name(db: Session, name: str):
    return db.query(models.M3U_User.name, models.M3U_User.password).filter(
        models.M3U_User.name == name
    ).first()


def insert_user(db: Session, form: UserFromForm):
    db_user = models.M3U_User(name=form.username, email=form.email,
                              password=form.password,
                              creation_date=datetime.now(), disabled='N')
    db.add(db_user)
    db.commit()
    # db.refresh()


def subs_name(pr_name):
    name = pr_name.rstrip().rstrip(')')
    pr_subs = ({'fhd': 'hd', 'россия-1': 'россия 1', 'твц': 'тв центр',
                '5 канал': 'пятый канал',
                'рен тв hd': 'рен тв', 'мир hd': 'мир',
                'телеканал звезда': 'звезда', 'тв3 hd': 'тв-3',
                'тв3': 'тв-3', 'пятница! hd': 'пятница',
                'пятница!': 'пятница'})
    for key in pr_subs:
        if key in name:
            name = name.replace(key, pr_subs[key])
            break
    # print(name)
    # pos = nm.find('hd')
    # if (pos > 0) :
    #     nm = nm[:pos].rstrip()
    shift = 0
    if '+' in name:
        pos = name.find('+')
        shift = int(name[pos:])
        name = name[:pos].rstrip('(').rstrip()
    elif (' -' or '(-') in name:
        pos = name.find('-')
        shift = int(name[pos:])
        name = name[:pos].rstrip('(').rstrip()
    return name, shift


def get_details(db: Session, name: str, dt: datetime):
    nm, shft = subs_name(name.lower())
    if shft:
        dt += timedelta(hours=shft)
    result = db.query(
        models.Programme).join(models.Channel).filter(
            models.Programme.pstart <= dt,
            models.Programme.pstop > dt,
            models.Channel.disp_name_l == nm
        ).first()
    result.disp_name = name
    if result and shft:
        result.pstart -= timedelta(hours=shft)
        result.pstop -= timedelta(hours=shft)
    return result
