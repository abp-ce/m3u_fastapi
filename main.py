import os
from datetime import datetime, timedelta
import urllib
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
from pydantic import BaseModel
import cx_Oracle
import M3Uclass
from crud import get_details, user_by_name, insert_user
from schemas import Programme_Response, User, UserFromForm, PersonalList, Token
from dependencies import get_current_active_user, authenticate_user, get_password_hash, create_access_token, get_db 
from telebot import telebot
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import Session, sessionmaker

ACCESS_TOKEN_EXPIRE_MINUTES = 30

"""
def get_db():
    return app.state.db
"""
app = FastAPI(dependencies=[Depends(get_db)])

app.include_router(telebot.router)

origins = [
    "https://localhost:8080",
    "http://localhost:8080",
    #"http://localhost.abp-te.tk:8080",
    "https://abp-ce.github.io",
    "https://api.telegram.org"
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
  app.state.db = cx_Oracle.SessionPool(user=os.getenv('ATP_USER'), password=os.getenv('ATP_PASSWORD'),
                            dsn=os.getenv('ATP_DSN'), min = 4, max = 4, increment=0, threaded=True)
  engine = create_engine("oracle://", creator=app.state.db.acquire, poolclass=NullPool)
  app.state.session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@app.on_event("shutdown")
def close_pool():
  app.state.db.close()

@app.post("/register", response_model=Token)
async def register_for_access_token(form_data: UserFromForm, db: Session = Depends(get_db)):
    result = user_by_name(db=db,name=form_data.username)
    if result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Username {result['name']} already exists",
            headers={"WWW-Authenticate": "Bearer"},
            )
    form_data.password = get_password_hash(form_data.password)
    insert_user(db=db,form=form_data)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": form_data.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="Bearer")

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
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
    #return {"access_token": access_token, "token_type": "Bearer"}

@app.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

@app.get("/users/me/items/")
async def read_own_items(current_user: User = Depends(get_current_active_user)):
    return [{"item_id": "Foo", "owner": current_user.username}]

@app.get("/{p_name}/{dt}", response_model = Programme_Response)
def details(p_name: str, dt: datetime, db: Session = Depends(get_db)):
  return get_details(db, p_name, dt)

@app.get("/load/")
def load(url: Optional[str] = None):
  if url:
    with urllib.request.urlopen(url) as f:
      lines = f.readlines()
    m3u = M3Uclass.M3U(lines)
    return m3u.get_dict_arr()
  return { 'message': 'Empty URL' }

@app.post("/save", response_class=FileResponse)
def save(per_list: List[PersonalList], current_user: User = Depends(get_current_active_user)):
    with open(f'../files/{current_user.username}.txt','w') as f:
      f.write("#EXTM3U\n")
      for ch in per_list:
          f.write(f'#EXTINF:-1 ,{ch.title}\n')
          f.write(f'{ch.value}\n')
    return f'../files/{current_user.username}.txt'

@app.get('/load_personal')
def load_personal(current_user: User = Depends(get_current_active_user)):
    if not os.path.exists(f'../files/{current_user.username}.txt'):
      return []
    with open(f'../files/{current_user.username}.txt','r') as f:
      lines = f.readlines()
    m3u = M3Uclass.M3U(lines)
    return m3u.get_dict_arr()


