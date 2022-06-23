import os
import xml.etree.ElementTree as Et
from datetime import datetime, timedelta
from urllib.request import urlretrieve

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from constants import DATABASE_NAME, FILE_NAME, FILE_URL
from models import Base, Channel, Programme

# import cx_Oracle


def retrieve_file():
    urlretrieve(FILE_URL, FILE_NAME + '.gz')
    if os.path.exists(FILE_NAME):
        os.remove(FILE_NAME)
    os.system('gunzip ' + FILE_NAME + '.gz')


def recreate_tables(db: Session) -> None:
    engine = db.get_bind()
    channel = Base.metadata.tables['channel']
    programme = Base.metadata.tables['programme']
    Base.metadata.drop_all(bind=engine, tables=[programme, channel],
                           checkfirst=True)
    Base.metadata.create_all(bind=engine, tables=[channel, programme])


def populate_epg_db(db: Session) -> None:
    retrieve_file()
    recreate_tables(db)
    cinsval, pinsval = [], []
    ccnt, pcnt = 0, 0
    flag = True
    for event, elem in Et.iterparse(FILE_NAME, events=("start", "end")):
        if elem.tag == "channel" and event == "end":
            ch_id = disp_name = icon = None
            ch_id = elem.attrib['id']
            for c in elem:
                if c.tag == 'display-name':
                    disp_name = c.text
                elif c.tag == 'icon':
                    icon = c.attrib['src']
            cinsval.append(Channel(ch_id=ch_id, disp_name=disp_name,
                                   disp_name_l=disp_name.lower(), icon=icon))
            ccnt += 1
            if ccnt == 1500:
                db.add_all(cinsval)
                db.commit()
                cinsval.clear()
                ccnt = 0
            elem.clear()
        if elem.tag == "programme" and event == "end":
            if flag:
                db.add_all(cinsval)
                db.commit()
                flag = False
            channel = pstart = pstop = title = pdesc = cat = None
            channel = elem.attrib['channel']
            st = elem.attrib['start']
            pstart = datetime(int(st[:4]), int(st[4:6]), int(st[6:8]),
                              int(st[8:10]), int(st[10:12]), int(st[12:14]))
            pstart -= timedelta(hours=int(st[14:18]), minutes=int(st[18:]))
            st = elem.attrib['stop']
            pstop = datetime(int(st[:4]), int(st[4:6]), int(st[6:8]),
                             int(st[8:10]), int(st[10:12]), int(st[12:14]))
            pstop -= timedelta(hours=int(st[14:18]), minutes=int(st[18:]))
            for c in elem:
                if c.tag == 'title':
                    title = c.text
                elif c.tag == 'desc':
                    pdesc = c.text
                elif c.tag == 'category':
                    cat = c.text
            pinsval.append(Programme(channel=channel, pstart=pstart,
                           pstop=pstop, title=title, pdesc=pdesc, cat=cat))
            pcnt += 1
            if (pcnt == 1500):
                db.add_all(pinsval)
                db.commit()
                pinsval.clear()
                pcnt = 0
            elem.clear()
    db.add_all(pinsval)
    db.commit()


if __name__ == "__main__":
    # connection = cx_Oracle.connect(user=os.getenv('ATP_USER'),
    #                                password=os.getenv('ATP_PASSWORD'),
    #                                dsn=os.getenv('ATP_DSN'))
    # cursor = connection.cursor()
    engine = create_engine('sqlite:///' + DATABASE_NAME)
    session = sessionmaker(autocommit=False, autoflush=False,
                           bind=engine)()
    populate_epg_db(session)
    print("EPG was successfully populated")
