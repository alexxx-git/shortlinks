from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
import asyncpg
import redis
from config import DATABASE_URL, REDIS_PASSWORD, REDIS_HOST, REDIS_PORT, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from auth import authenticate_user, fake_users_db  # Импортируем авторизацию

app = FastAPI()

# Подключение к Redis
redis_client = redis.StrictRedis(
    host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, decode_responses=True
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Подключение к базе данных
async def connect_to_db():
    return await asyncpg.connect(DATABASE_URL)

def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=30)):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta  # Исправил на UTC
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me")
async def read_users_me(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=403, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=403, detail="Invalid token")
    
    return {"username": username}

@app.get("/protected")
async def protected_route(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=403, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=403, detail="Invalid token")
    
    return {"message": f"Hello, {username}"}
