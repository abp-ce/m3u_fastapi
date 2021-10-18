import os
from datetime import datetime, timedelta
import urllib
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from passlib.context import CryptContext
from typing import Optional
from pydantic import BaseModel
import cx_Oracle
import M3Uclass
from crud import user_by_name, insert_user

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

def get_user(db, username: str):
    #if username in db:
    connection = app.state.db.acquire()
    result = user_by_name(connection.cursor(),username)
    app.state.db.release(connection)
    if result: return UserInDB(username = result['name'], hashed_password = result['password'])
    return result

        #user_dict = db[username]
        #return UserInDB(**user_dict)


def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
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
    user = get_user(fake_users_db, username=token_data.username)
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
    return {"access_token": access_token, "token_type": "bearer"}

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
    return {"access_token": access_token, "token_type": "bearer"}

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

@app.get("/{p_name}/{dt}")
def details(p_name: str, dt: datetime):
  nm, shft = subs_name(p_name.lower())
  connection = app.state.db.acquire()
  with connection.cursor() as cursor:
    dt += timedelta(hours=shft)
    cursor.execute('SELECT c.disp_name, pstart, pstop, title, pdesc FROM programme p JOIN channel c '
                 'ON p.channel = c.ch_id WHERE disp_name_l = :1 AND pstart < :2 AND pstop > :3 ORDER BY pstart', 
                 (nm, dt, dt))
    cursor.rowfactory = lambda *args: dict(zip([d[0].lower() for d in cursor.description], args))
    result = cursor.fetchone()
    if (result):
      result['pstart'] -= timedelta(hours=shft)  
      result['pstop'] -= timedelta(hours=shft)  
  app.state.db.release(connection)
  return result

@app.get("/load/")
def load(url: Optional[str] = None):
  #print(url)
  if url:
    with urllib.request.urlopen(url) as f:
      lines = f.readlines()
    m3u = M3Uclass.M3U(lines)
    return m3u.get_dict_arr()
  return { 'message': 'Empty URL' }
  