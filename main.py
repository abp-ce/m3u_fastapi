import os
import urllib
from datetime import datetime, timedelta
from typing import List, Optional

import cx_Oracle
from dotenv import load_dotenv
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from constants import (ACCESS_TOKEN_EXPIRE_MINUTES,
                       DATABASE_NAME, DATABASE_TYPE)
from crud import get_details, insert_user, user_by_name
from dependencies import (authenticate_user, create_access_token,
                          get_current_active_user, get_db, get_password_hash)
import M3Uclass
from populate_epg_db import populate_epg_db
from schemas import (PersonalList, Programme_Response, Token, User,
                     UserFromForm)
from telebot import telebot

"""
def get_db():
    return app.state.db
"""
load_dotenv()

app = FastAPI(dependencies=[Depends(get_db)])

app.include_router(telebot.router)

origins = [
    "https://localhost:8080",
    "http://localhost:48080",
    "http://localhost:8080",
    # "http://a.abp-te.tk:48892",
    "https://abp-ce.github.io",
    "https://api.telegram.org",
    "http://abp-m3u.ml",
    "https://abp-m3u.ml"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def create_pool():
    if DATABASE_TYPE == 'SQLITE':
        app.state.db = None
        engine = create_engine(
            'sqlite:///' + DATABASE_NAME,
            connect_args={'check_same_thread': False}
        )
    else:
        app.state.db = cx_Oracle.SessionPool(
            user=os.getenv('ATP_USER'),
            password=os.getenv('ATP_PASSWORD'),
            dsn=os.getenv('ATP_DSN'),
            min=4,
            max=4,
            increment=0,
            threaded=True
        )
        engine = create_engine("oracle://", creator=app.state.db.acquire,
                               poolclass=NullPool)
    app.state.session = sessionmaker(autocommit=False, autoflush=False,
                                     bind=engine)


@app.on_event("shutdown")
def close_pool():
    if app.state.db:
        app.state.db.close()


@app.post("/register", response_model=Token)
async def register_for_access_token(form_data: UserFromForm,
                                    db: Session = Depends(get_db)):
    result = user_by_name(db=db, name=form_data.username)
    if result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Username {result['name']} already exists",
            headers={"WWW-Authenticate": "Bearer"},
            )
    form_data.password = get_password_hash(form_data.password)
    insert_user(db=db, form=form_data)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": form_data.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="Bearer")


@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="Bearer")
    # return {"access_token": access_token, "token_type": "Bearer"}


@app.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user


@app.get("/users/me/items/")
async def read_own_items(
    current_user: User = Depends(get_current_active_user)
):
    return [{"item_id": "Foo", "owner": current_user.username}]


@app.get("/{p_name}/{dt}", response_model=Programme_Response)
def details(p_name: str, dt: datetime, db: Session = Depends(get_db)):
    return get_details(db, p_name, dt)


@app.get("/load/")
def load(url: Optional[str] = None):
    if url:
        with urllib.request.urlopen(url) as f:
            lines = f.readlines()
        m3u = M3Uclass.M3U(lines)
        return m3u.get_dict_arr()
    return {'message': 'Empty URL'}


@app.post("/save", response_class=FileResponse)
def save(
    per_list: List[PersonalList],
    current_user: User = Depends(get_current_active_user)
):
    with open(f'../files/{current_user.username}.txt', 'w') as f:
        f.write("#EXTM3U\n")
        for ch in per_list:
            f.write(f'#EXTINF:-1 ,{ch.title}\n')
            f.write(f'{ch.value}\n')
    return f'../files/{current_user.username}.txt'


@app.get('/load_personal')
def load_personal(current_user: User = Depends(get_current_active_user)):
    if not os.path.exists(f'../files/{current_user.username}.txt'):
        return []
    with open(f'../files/{current_user.username}.txt', 'r') as f:
        lines = f.readlines()
    m3u = M3Uclass.M3U(lines)
    return m3u.get_dict_arr()


@app.get('/refresh_epg_db')
def refresh_epg_db(background_tasks: BackgroundTasks,
                   db: Session = Depends(get_db)):
    background_tasks.add_task(populate_epg_db, db)
    return {"message": "Refreshing EPG db in the background"}
