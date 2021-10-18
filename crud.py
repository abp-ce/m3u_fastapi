import cx_Oracle
from datetime import datetime, timedelta
import urllib

def user_by_name(cursor, name):
    cursor.execute('SELECT name, password FROM m3u_users WHERE name = :1',(name,))
    cursor.rowfactory = lambda *args: dict(zip([d[0].lower() for d in cursor.description], args))
    return cursor.fetchone()

def insert_user(cursor, form):
    cursor.execute('INSERT INTO m3u_users(name, email, password, creation_date, disabled) VALUES ( :1, :2, :3, :4, :5)',
        (form.username, form.email, form.password, datetime.now(), 'N',))

