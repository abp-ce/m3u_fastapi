import cx_Oracle
from datetime import datetime, timedelta
import M3Uclass
import urllib

def user_by_name(cursor, name):
    cursor.execute('SELECT name, password FROM m3u_users WHERE name = :1',(name,))
    cursor.rowfactory = lambda *args: dict(zip([d[0].lower() for d in cursor.description], args))
    return cursor.fetchone()

def insert_user(cursor, form):
    cursor.execute('INSERT INTO m3u_users(name, email, password, creation_date, disabled) VALUES ( :1, :2, :3, :4, :5)',
        (form.username, form.email, form.password, datetime.now(), 'N',))

def subs_name(pr_name):
    name = pr_name.rstrip().rstrip(')')
    pr_subs = ({ 'fhd': 'hd', 'россия-1': 'россия 1', 'твц': 'тв центр', '5 канал': 'пятый канал',
              'рен тв hd': 'рен тв', 'мир hd': 'мир', 'телеканал звезда': 'звезда', 'тв3 hd': 'тв-3',
              'тв3': 'тв-3', 'пятница! hd': 'пятница', 'пятница!': 'пятница' })
    for key in pr_subs:
        if key in name : 
            name = name.replace(key,pr_subs[key])
            break
    #print(name)
    #pos = nm.find('hd')
    #if (pos > 0) :
    #    nm = nm[:pos].rstrip()
    shift = 0
    if '+' in name : 
        pos = name.find('+')
        shift = int(name[pos:])
        name = name[:pos].rstrip('(').rstrip()
    elif (' -' or '(-') in name : 
        pos = name.find('-')
        shift = int(name[pos:])
        name = name[:pos].rstrip('(').rstrip()
    return name, shift

def get_details(cursor, name, dt):
    nm, shft = subs_name(name.lower())
    dt += timedelta(hours=shft)
    cursor.execute('SELECT c.disp_name, pstart, pstop, title, pdesc FROM programme p JOIN channel c '
                 'ON p.channel = c.ch_id WHERE disp_name_l = :1 AND pstart < :2 AND pstop > :3 ORDER BY pstart', 
                 (nm, dt, dt))
    cursor.rowfactory = lambda *args: dict(zip([d[0].lower() for d in cursor.description], args))
    result = cursor.fetchone()
    if (result):
      result['pstart'] -= timedelta(hours=shft)  
      result['pstop'] -= timedelta(hours=shft)  
    return result
