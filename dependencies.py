
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status, Request
from jose import JWTError, jwt
from sqlalchemy.orm.session import Session
from crud import get_details, user_by_name, insert_user, get_details
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from typing import Optional, List
from schemas import User, UserInDB, TokenData

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "5de0583b39744f1c654a91a159cd363bd2fcd7fb619ea066f4c4ecf12c98df83"
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_db(request: Request):
    db = request.app.state.session()
    try:
        yield db
    finally:
        db.close()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(db: Session, username: str):
    #connection = db.acquire()
    result = user_by_name(db=db,name=username)
    #db.release(connection)
    if result: return UserInDB(username = result['name'], hashed_password = result['password'])
    return result


def authenticate_user(username: str, password: str, db: Session):
    user = get_user(db=db, username=username)
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

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
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
    user = get_user(db=db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

