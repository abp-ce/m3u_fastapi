import os
from datetime import datetime, timedelta
import urllib
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
from pydantic import BaseModel
import cx_Oracle
import M3Uclass
from crud import get_details, user_by_name, insert_user
from dependencies import User, get_current_active_user, authenticate_user, Token, get_password_hash, create_access_token

ACCESS_TOKEN_EXPIRE_MINUTES = 30

class UserFromForm(User):
    password: str

class PersonalList(BaseModel):
    title: str
    value: str

def get_db():
    return app.state.db

app = FastAPI(dependencies=[Depends(get_db)])

origins = [
    "https://localhost:8080",
    "http://localhost:8080",
    "http://abp-oci2.tk:80",
    "https://abp-oci2.tk:80",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=[*],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def create_pool():
  app.state.db = cx_Oracle.SessionPool(user=os.getenv('ATP_USER'), password=os.getenv('ATP_PASSWORD'),
                            dsn=os.getenv('ATP_DSN'), min = 4, max = 4, increment=0, threaded=True)

@app.on_event("shutdown")
def close_pool():
  app.state.db.close()

@app.post("/register", response_model=Token)
async def register_for_access_token(form_data: UserFromForm):
    connection = app.state.db.acquire()
    result = user_by_name(connection.cursor(),form_data.username)
    if result:
        app.state.db.release(connection)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Username {result['name']} already exists",
            headers={"WWW-Authenticate": "Bearer"},
            )
    form_data.password = get_password_hash(form_data.password)
    insert_user(connection.cursor(),form_data)
    connection.commit()
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": form_data.username}, expires_delta=access_token_expires
    )
    app.state.db.release(connection)
    return {"access_token": access_token, "token_type": "Bearer"}

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password, app.state.db)
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
    return {"access_token": access_token, "token_type": "Bearer"}

@app.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

@app.get("/users/me/items/")
async def read_own_items(current_user: User = Depends(get_current_active_user)):
    return [{"item_id": "Foo", "owner": current_user.username}]

@app.get("/{p_name}/{dt}")
def details(p_name: str, dt: datetime):
  connection = app.state.db.acquire()
  result = get_details(connection.cursor(), p_name, dt)
  app.state.db.release(connection)
  return result

@app.get("/load/")
def load(url: Optional[str] = None):
  if url:
    with urllib.request.urlopen(url) as f:
      lines = f.readlines()
    m3u = M3Uclass.M3U(lines)
    return m3u.get_dict_arr()
  return { 'message': 'Empty URL' }

@app.post("/save")
def save(per_list: List[PersonalList], current_user: User = Depends(get_current_active_user)):
    #print(current_user.username)
    with open(f'../files/{current_user.username}.txt','w') as f:
      f.write("#EXTM3U\n")
      for ch in per_list:
          f.write(f'#EXTINF:-1 ,{ch.title}\n')
          f.write(f'{ch.value}\n')
    return 1

@app.get('/load_personal')
def load_personal(current_user: User = Depends(get_current_active_user)):
    if not os.path.exists(f'../files/{current_user.username}.txt'):
      return []
    with open(f'../files/{current_user.username}.txt','r') as f:
      lines = f.readlines()
    m3u = M3Uclass.M3U(lines)
    return m3u.get_dict_arr()


