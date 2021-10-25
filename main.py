import os
from datetime import datetime, timedelta
import urllib
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from passlib.context import CryptContext
from typing import Optional, List
from pydantic import BaseModel
import cx_Oracle
import M3Uclass
from crud import get_details, user_by_name, insert_user, get_details

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "5de0583b39744f1c654a91a159cd363bd2fcd7fb619ea066f4c4ecf12c98df83"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        "disabled": False,
    },
    "alice": {
        "username": "alice",
        "full_name": "Alice Wonderson",
        "email": "alice@example.com",
        "hashed_password": "fakehashedsecret2",
        "disabled": True,
    },
}

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None

class UserInDB(User):
    hashed_password: str

class UserFromForm(User):
    password: str

class PersonalList(BaseModel):
    title: str
    value: str

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()

origins = [
    "https://localhost:8080",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(username: str):
    #if username in db:
    connection = app.state.db.acquire()
    result = user_by_name(connection.cursor(),username)
    app.state.db.release(connection)
    if result: return UserInDB(username = result['name'], hashed_password = result['password'])
    return result

        #user_dict = db[username]
        #return UserInDB(**user_dict)


def authenticate_user(fake_db, username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@app.post("/register", response_model=Token)
async def register_for_access_token(form_data: UserFromForm):
#async def register_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
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
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
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

@app.on_event("startup")
def create_pool():
  app.state.db = cx_Oracle.SessionPool(user=os.getenv('ATP_USER'), password=os.getenv('ATP_PASSWORD'),
                            dsn=os.getenv('ATP_DSN'), min = 4, max = 4, increment=0, threaded=True)

@app.on_event("shutdown")
def close_pool():
  app.state.db.close()

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


