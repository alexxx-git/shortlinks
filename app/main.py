# Стандартная библиотека и встроенные модули

from datetime import datetime, timedelta, timezone
from contextlib import asynccontextmanager
from typing import Optional
from urllib.parse import urlparse, parse_qs, urlencode, unquote, quote
import asyncio
import re
import string
import hashlib
import random

# FastAPI и связанные компоненты
from fastapi import (
    FastAPI, Depends, HTTPException, Request, 
    Form, Cookie, status,  Header
)
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

# Базы данных и ORM
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, delete, update
from sqlalchemy.orm import joinedload

# Модели и схемы
from app.models import User, ShortLink, ShortLinkArchive, Visit, VisitArchive
from app.schemas import LinkRequest, ShortLinkUpdateModel, ArchiveFilter

# Аутентификация и безопасность
from app.auth import hash_password, verify_password
from jose import jwt, JWTError
from app.config import (
    SECRET_KEY, 
    ALGORITHM, 
    ACCESS_TOKEN_EXPIRE_MINUTES, 
    LINK_EXPIRE_TIME_IN_DAYS_4UNREG, 
    LINK_EXPIRE_TIME_IN_DAYS_REG,
    REDIS_TTL
)

# Внешние сервисы и утилиты
from app.database import get_db, engine
from app.redis_cache import get_redis, redis_dependency
from redis.asyncio import Redis
import geoip2.database

# Pydantic для валидации
from pydantic import HttpUrl




app = FastAPI()
templates = Jinja2Templates(directory="app/templates")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="app/token")

@asynccontextmanager
async def lifespan(app: FastAPI):
      # Подключение к Redis (с await!)
    get_redis()
      # Инициализация БД
    async with engine.begin() as conn:
        await conn.run_sync(User.metadata.create_all)
    
    yield  # Здесь приложение работает


app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="app/templates/static"), name="static")

def random_salt():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))


def generate_short_code(original_url: HttpUrl) -> str:
    original_url_str = str(original_url)  # Преобразуем HttpUrl в строку
    hash_value = hashlib.sha256((original_url_str + random_salt()).encode()).hexdigest()
    return hash_value[:8]  # Обрезаем до 8 символов

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, token: str = Cookie(None)):
    username = None
    if token:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username = payload.get("sub")
        except JWTError:
            pass
    return templates.TemplateResponse("index.html", {"request": request, "username": username})

@app.get("/users/me")
async def read_users_me(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=403, detail="Неверный токен")
    except JWTError:
        raise HTTPException(status_code=403, detail="Неверный токен")

    return {"username": username}




# Функция для получения user_id из токена
async def get_user_from_token(
    token: Optional[str] = Header(None, alias="Authorization"),  
    db: AsyncSession = Depends(get_db)
) -> Optional[int]:
    if not token:
        print("Токен отсутствует!")
        return None  

    # Убираем "Bearer " из токена, чтобы оставить только сам токен
    token = token.replace("Bearer ", "").strip()
    
    try:
        print(f"Полученный токен: {token}")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub")
        if not username:
            print("Токен не содержит username!")
            return None  
    except JWTError as e:
        print(f"Ошибка декодирования JWT: {e}")
        return None  

    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if not user:
        print(f"Пользователь {username} не найден!")
        return None  

    print(f"Авторизованный user_id: {user.id}")
    return user.id

def extract_expires_at(original_url: str):
    """
    Извлекает параметр `expires_at` из URL и возвращает (чистый URL, datetime или None)
    """
    parsed_url = urlparse(original_url)  # Разбираем URL
    query_params = parse_qs(parsed_url.query)  # Извлекаем параметры

    expires_at = None
    if "expires_at" in query_params:
        expires_at_values = query_params["expires_at"]
        if expires_at_values:
            try:
                expires_at = datetime.fromisoformat(expires_at_values[-1])  # Берем последний параметр
            except ValueError:
                pass  # Если неверный формат, просто пропускаем

    # Удаляем `expires_at` из параметров и собираем URL обратно
    filtered_params = {k: v for k, v in query_params.items() if k != "expires_at"}
    new_query_string = urlencode(filtered_params, doseq=True)
    cleaned_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
    if new_query_string:
        cleaned_url += f"?{new_query_string}"

    return cleaned_url, expires_at

def encode_url(url: str) -> str:
    """Кодирует URL для безопасного хранения в Redis"""
    return quote(url, safe='')

def decode_url(encoded_url: str) -> str:
    """Декодирует URL из Redis"""
    return unquote(encoded_url)



@app.post("/links/shorten")
async def shorten_link(
    request: Request,
    link_request: LinkRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(redis_dependency),
    user_id: Optional[int] = Depends(get_user_from_token),
):
    cleaned_url, expires_at_query = extract_expires_at(link_request.original_url)

    short_code = link_request.customAlias

    if not user_id and not expires_at_query:
        redis_key = f"longlink:{quote(cleaned_url)}"  
        existing_short_code = await redis.get(redis_key)

        if existing_short_code:
            # Добавлена проверка в базу данных для незарегистрированных пользователей
            db_query = select(ShortLink).where(
                ShortLink.short_code == existing_short_code,
                ShortLink.user_id.is_(None)  # Проверяем только у незарегистрированных
            )
            db_result = await db.execute(db_query)
            if db_result.scalars().first():
                short_code = existing_short_code
                await redis.expire(redis_key, REDIS_TTL)
                await redis.expire(f"shortlink:{short_code}", REDIS_TTL)
                
                host = str(request.base_url).rstrip("/")
                return {
                    "short_url": f"{host}/links/{short_code}",
                    "original_url": cleaned_url,
                    "custom_alias": short_code,
                    "from_cache": True
                }

    if short_code:
        redis_key = f"shortlink:{quote(short_code)}" 

        if await redis.exists(redis_key):
            raise HTTPException(status_code=400, detail="This alias is already taken. Please choose another.")

        query = select(ShortLink).where(ShortLink.short_code == short_code)
        result = await db.execute(query)
        if result.scalars().first():
            raise HTTPException(status_code=400, detail="This alias is already taken. Please choose another.")

    else:
        while True:
            short_code = generate_short_code(cleaned_url)
            redis_key = f"shortlink:{quote(short_code)}"  

            if await redis.exists(redis_key):
                continue

            query = select(ShortLink).where(ShortLink.short_code == short_code)
            result = await db.execute(query)
            if result.scalars().first():
                continue

            break 

    encoded_url = quote(cleaned_url)  

    if expires_at_query:
        ttl = min((expires_at_query - datetime.now()).total_seconds(), REDIS_TTL)
    else:
        ttl = REDIS_TTL

    await redis.set(f"shortlink:{quote(short_code)}", encoded_url, ex=int(ttl)) 
    await redis.set(f"longlink:{encoded_url}", quote(short_code), ex=int(ttl)) 

    if expires_at_query:
        auto_expires = None  
        expires_at = expires_at_query
    else:
        auto_expires = datetime.now() + timedelta(days=LINK_EXPIRE_TIME_IN_DAYS_REG) if user_id else datetime.now() + timedelta(days=LINK_EXPIRE_TIME_IN_DAYS_4UNREG)
        expires_at = None

    new_link = ShortLink(
        short_code=short_code,
        original_url=cleaned_url,  
        created_at=datetime.now(),
        expires_at=expires_at,
        user_id=user_id,
        auto_expires_at=auto_expires
    )
    db.add(new_link)
    await db.commit()

    host = str(request.base_url).rstrip("/")
    short_url = f"{host}/links/{short_code}"

    return {
        "short_url": short_url,
        "original_url": cleaned_url,
        "custom_alias": short_code
    }


@app.post("/register")
async def register_user(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await db.execute(select(User).where((User.username == username) | (User.email == email)))
        existing_user = result.scalars().first()

        if existing_user:
            if existing_user.username == username:
                raise HTTPException(status_code=400, detail="Имя пользователя уже занято")
            if existing_user.email == email:
                raise HTTPException(status_code=400, detail="Email уже зарегистрирован")

        # Создаём нового пользователя
        new_user = User(username=username, email=email, password=hash_password(password))
        db.add(new_user)
        await db.commit()

        # Возвращаем JSON вместо редиректа
        return JSONResponse(content={"message": "Регистрация успешна", "username": username}, status_code=200)

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Ошибка при регистрации: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")



@app.post("/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    # Поиск пользователя
    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalars().first()

    # Проверка учетных данных
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Генерация токена
    access_token = jwt.encode(
        {
            "sub": user.username,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        },
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    # Определяем тип клиента
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
    


@app.get("/logout")
async def logout():
    # Удаляем токен из куки
    response = RedirectResponse(url="/")
    response.delete_cookie("token")  # Удаляем куки
    return response



# Инициализация GeoIP2
reader = geoip2.database.Reader('app/GeoLite2-Country.mmdb')

def get_country_by_ip(ip: str) -> str:
    try:
        response = reader.country(ip)
        return response.country.iso_code  # Например, 'US', 'RU'
    except:
        return None  # Если IP не определён


def parse_domains(url: str):
    """Парсит домен 1-го (зона, например, com, ru) и 2-го уровня (example.com) через urlparse."""
    parsed_url = urlparse(url)
    hostname = parsed_url.hostname  # Например, "sub.example.com"

    if not hostname:
        return None, None

    parts = hostname.split(".")

    if len(parts) >= 2:
        domain_1st = parts[-1]  # Зона (TLD), например, "com", "ru"
        domain_2nd = ".".join(parts[-2:])  # Домен второго уровня, например, "example.com"
    else:
        domain_1st = hostname
        domain_2nd = hostname

    return domain_1st, domain_2nd



@app.delete("/links/{short_code}")
async def delete_short_link(
    short_code: str,
    user_id: int = Depends(get_user_from_token),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(redis_dependency),
):
    print(f"Получен запрос на удаление ссылки с кодом: {short_code} от пользователя с ID: {user_id}")
    
    if user_id is None:
        return {"Ошибка": "Попытка удалить ссылку неавторизованным пользователем."}

    try:
        query = select(ShortLink).where(ShortLink.short_code == short_code, ShortLink.user_id == user_id)
        result = await db.execute(query)
        short_link = result.scalars().first()

        if not short_link:
            return {"Ошибка": "Ссылка не найдена или у вас нет прав на ее удаление."}

        archived_link = ShortLinkArchive(
            user_id=short_link.user_id,
            short_code=short_link.short_code,
            original_url=short_link.original_url,
            created_at=short_link.created_at,
            expires_at=short_link.expires_at,
            last_access_at=short_link.last_access_at,
            auto_expires_at=short_link.auto_expires_at,
            archived_at=datetime.now(),
            archival_reason="deleted"
        )
        db.add(archived_link)

        query_visits = select(Visit).where(Visit.short_code == short_code)
        result_visits = await db.execute(query_visits)
        visits = result_visits.scalars().all()

        if visits:
            
            for visit in visits:
                visit_archive = VisitArchive(
                    owner=visit.owner,
                    timestamp=visit.timestamp,
                    short_code=visit.short_code,
                    original_url=visit.original_url,
                    domain_1st=visit.domain_1st,
                    domain_2nd=visit.domain_2nd,
                    ip_address=visit.ip_address,
                    device_type=visit.device_type,
                    country=visit.country,
                    referer=visit.referer,
                    archived_at=datetime.now(),
                    archival_reason="deleted"
                )
                db.add(visit_archive)
                await db.delete(visit) 

        else:
            print(f"Визитов для ссылки {short_code} не найдено.")

        await db.delete(short_link)

        await redis.delete(f"shortlink:{short_code}")
        await redis.delete(f"short_ui:{short_code}")

        await db.commit()
        
    except Exception as e:
        await db.rollback()
        return {"error": f"Произошла ошибка при удалении ссылки: {str(e)}"}

    return {"Сообщение": "Данные ссылки и посещений заархивированы и стёрты."}




from pydantic import BaseModel, Field, field_validator
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
import re

class ShortLinkUpdateModel(BaseModel):
    new_url: str = Field(..., max_length=2000)

    @field_validator('new_url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not re.match(r"^https?://", v):
            raise ValueError('Некорректный URL')
        return v.strip()

@app.put("/links/{short_code}")
async def update_short_link(
    short_code: str,
    link_update: ShortLinkUpdateModel,  
    user_id: int = Depends(get_user_from_token),
    redis: Redis = Depends(redis_dependency),
    db: AsyncSession = Depends(get_db),
):

    new_url = link_update.new_url


    query = select(ShortLink).where(
        ShortLink.short_code == short_code,
        ShortLink.user_id == user_id
    )
    result = await db.execute(query)
    short_link = result.scalars().first()

    if not short_link:
        raise HTTPException(
            status_code=404,
            detail="Ссылка не найдена или у вас нет прав на её изменение"
        )

    old_encoded_url = encode_url(short_link.original_url)
    short_link.original_url = new_url
    short_link.created_at = datetime.utcnow()
    short_link.auto_expires_at = datetime.utcnow() + timedelta(days=LINK_EXPIRE_TIME_IN_DAYS_REG)


    if hasattr(short_link, 'last_access_at'):
        short_link.last_access_at = None
    if hasattr(short_link, 'expires_at'):
        short_link.expires_at = None


    new_encoded_url = encode_url(new_url)
    await redis.delete(f"longlink:{old_encoded_url}")
    await redis.delete(f"shortlink:{short_code}")
    await redis.set(f"shortlink:{short_code}", new_encoded_url, ex=int(REDIS_TTL))
    await redis.set(f"longlink:{new_encoded_url}", short_code, ex=int(REDIS_TTL))

    await db.commit()

    return {
        "short_code": short_code,
        "new_url": new_url,
        "message": "Ссылка успешно обновлена",
        "auto_expires_at": short_link.auto_expires_at.isoformat() if short_link.auto_expires_at else None
    }

# ***************************************************************************************************************


@app.get("/links/{short_code}/stats")
async def get_link_stats(
    short_code: str,
    db: AsyncSession = Depends(get_db),
):
    print(f"[DEBUG] Запрос статистики для короткой ссылки: {short_code}")


    query = select(ShortLink).where(ShortLink.short_code == short_code)
    result = await db.execute(query)
    short_link = result.scalars().first()

    if not short_link:
        print(f"[ERROR] Короткая ссылка {short_code} не найдена в базе данных")
        raise HTTPException(status_code=404, detail="Short link not found")

    print(f"[INFO] Найдена ссылка в БД: {short_link.short_code}")

  
    visit_query = select(func.count()).where(Visit.short_code == short_code)
    visit_result = await db.execute(visit_query)
    visit_count = visit_result.scalar()  

    stats = {
        "original_url": short_link.original_url,
        "created_at": short_link.created_at,
        "visit_count": visit_count,  
        "last_access_at": short_link.last_access_at,  
    }

    print(f"[INFO] Статистика для короткой ссылки {short_code}: {stats}")

    return stats







# ***************************************************************************************************************

@app.get("/links/search")
async def search_short_link(
    original_url: str,  # Параметр снова 'original_url'
    redis: Redis = Depends(redis_dependency),
    db: AsyncSession = Depends(get_db),
):

    print(f"[DEBUG] Переданный original_url: {original_url}")

    # Валидация URL
    if not re.match(r"^https?://", original_url):
        print(f"[ERROR] Некорректный URL: {original_url}")
        raise HTTPException(status_code=400, detail="Некорректный URL")


    encoded_url = encode_url(original_url)
    cached_short_code = await redis.get(f"longlink:{encoded_url}")

    if cached_short_code:
        short_code = decode_url(cached_short_code)  # Декодируем из Redis
        return {"short_code": short_code, "original_url": original_url}

    query = (
        select(ShortLink)
        .where(ShortLink.original_url == original_url)
        .order_by(ShortLink.created_at.desc())  # Берем самую свежую
    )
    result = await db.execute(query)
    short_link = result.scalars().first()

    if not short_link:
        raise HTTPException(status_code=404, detail="Short link not found for the provided URL")

    await redis.set(f"longlink:{encoded_url}", encode_url(short_link.short_code))


    return {"short_code": short_link.short_code, "original_url": short_link.original_url}



# ***************************************************************************************************************

@app.get("/links/{short_code}")
async def redirect_to_original_link(
    short_code: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(redis_dependency),
):
    redis_key = f"shortlink:{short_code}"
    user_cache_key = f"short_ui:{short_code}"  


    user_id = await redis.get(user_cache_key)
    if user_id is None:

        query = select(ShortLink.user_id).where(ShortLink.short_code == short_code)
        result = await db.execute(query)
        user_id = result.scalar()


        if user_id is None:
            user_id = None  


        await redis.set(user_cache_key, str(user_id) if user_id is not None else "guest", ex=REDIS_TTL)
    else:
        user_id = None if user_id == "guest" else int(user_id)


    encoded_url = await redis.get(redis_key)

    if encoded_url:
        original_url = decode_url(encoded_url)
        await redis.expire(redis_key, REDIS_TTL)
        await redis.expire(f"longlink:{encoded_url}", REDIS_TTL)
    else:

        query = select(ShortLink).where(ShortLink.short_code == short_code)
        result = await db.execute(query)
        short_link = result.scalars().first()

        if not short_link:
            return RedirectResponse("https://www.google.com/")  # Редирект на Google

        original_url = short_link.original_url
        await redis.set(redis_key, encode_url(original_url), ex=REDIS_TTL)


    ip_address = request.client.host if request.client else "unknown"


    country = get_country_by_ip(ip_address)


    user_agent = request.headers.get("User-Agent", "").lower()
    device_type = "mobile" if "mobile" in user_agent else "desktop"

    domain_1st, domain_2nd = parse_domains(original_url)


    visit = Visit(
        owner=user_id,
        timestamp=datetime.now(),
        short_code=short_code,
        original_url=original_url,
        domain_1st=domain_1st,
        domain_2nd=domain_2nd,
        ip_address=ip_address,
        device_type=device_type,
        country=country,
        referer=request.headers.get("Referer"),
    )
    db.add(visit)

    # ОБНОВЛЯЕМ last_access_at ДЛЯ ВСЕХ ССЫЛОК
    await db.execute(
        update(ShortLink)
        .where(ShortLink.short_code == short_code)
        .values(last_access_at=datetime.now())
    )

    await db.commit()  # Один коммит для всех изменений

    return RedirectResponse(original_url)



@app.get("/archive/stats")
async def get_archived_stats(
    filter: ArchiveFilter,
    user_id: int = Depends(get_user_from_token),
    db: AsyncSession = Depends(get_db)
):
    query = select(VisitArchive).where(VisitArchive.owner == user_id)


    if filter.short_code:
        query = query.where(VisitArchive.short_code == filter.short_code)

    result = await db.execute(query)
    visits = result.scalars().all()


    grouped_stats = {}
    for visit in visits:
        key = (visit.short_code, visit.original_url)
        if key not in grouped_stats:
            grouped_stats[key] = []
        grouped_stats[key].append({
            "timestamp": visit.timestamp,
            "domain_1st": visit.domain_1st,
            "domain_2nd": visit.domain_2nd,
            "ip_address": visit.ip_address,
            "device_type": visit.device_type,
            "country": visit.country,
            "referer": visit.referer,
            "archived_at": visit.archived_at,
            "archival_reason": visit.archival_reason
        })

    return grouped_stats



@app.get("/active-links/stats")
async def get_active_link_stats(
    filter: ArchiveFilter,  
    user_id: int = Depends(get_user_from_token),  
    db: AsyncSession = Depends(get_db),
):

    if not user_id:
        raise HTTPException(status_code=401, detail="Неавторизованный доступ")


    query = select(Visit).where(Visit.owner == user_id)


    if filter.short_code:
        query = query.where(Visit.short_code == filter.short_code)

    result = await db.execute(query)
    visits = result.scalars().all()

    if not visits:
        raise HTTPException(status_code=404, detail="Не найдено активных визитов для данного пользователя")


    grouped_stats = {}
    for visit in visits:
        key = (visit.short_code, visit.original_url)
        if key not in grouped_stats:
            grouped_stats[key] = []
        grouped_stats[key].append({
            "timestamp": visit.timestamp.isoformat(),
            "domain_1st": visit.domain_1st,
            "domain_2nd": visit.domain_2nd,
            "ip_address": visit.ip_address,
            "device_type": visit.device_type,
            "country": visit.country,
            "referer": visit.referer
        })

    return grouped_stats




async def archive_expired_links():
    period=60 #время между проверками удаляем каждую минуту т.к. есть задача  удаления ссылки с точностьбю до минуты
    """Фоновая задача для архивации устаревших ссылок и визитов и очистки Redis."""
    while True:
        async with get_db() as db, get_redis() as redis:
            now = datetime.now()

            try:
                # 1. Выбираем ссылки с истекшим сроком
                query = (
                    select(ShortLink)
                    .where((ShortLink.auto_expires_at < now) | (ShortLink.expires_at < now))
                    .options(joinedload(ShortLink.visits))  # Загружаем визиты сразу
                )
                result = await db.execute(query)
                expired_links = result.scalars().all()

                if not expired_links:
                    await asyncio.sleep(period)  # Если нет устаревших, ждем 
                    continue

                archived_links = []
                archived_visits = []
                short_codes_to_delete = set()

                for link in expired_links:
                    reason = "auto exp" if link.auto_expires_at < now else "exp"

                    archived_links.append(
                        ShortLinkArchive(
                            user_id=link.user_id,
                            short_code=link.short_code,
                            original_url=link.original_url,
                            created_at=link.created_at,
                            expires_at=link.expires_at,
                            last_access_at=link.last_access_at,
                            auto_expires_at=link.auto_expires_at,
                            archived_at=datetime.now(),
                            archival_reason=reason
                        )
                    )

                    for visit in link.visits:
                        archived_visits.append(
                            VisitArchive(
                                owner=visit.owner,
                                timestamp=visit.timestamp,
                                short_code=visit.short_code,
                                original_url=visit.original_url,
                                domain_1st=visit.domain_1st,
                                domain_2nd=visit.domain_2nd,
                                ip_address=visit.ip_address,
                                device_type=visit.device_type,
                                country=visit.country,
                                referer=visit.referer,
                                archived_at=datetime.now(),
                                archival_reason=reason
                            )
                        )

                    short_codes_to_delete.add(link.short_code)

                db.add_all(archived_links)
                db.add_all(archived_visits)

                await db.execute(delete(Visit).where(Visit.short_code.in_(short_codes_to_delete)))
                await db.execute(delete(ShortLink).where(ShortLink.short_code.in_(short_codes_to_delete)))

                for short_code in short_codes_to_delete:
                    original_url = await redis.get(f"shortlink:{short_code}")
                    if original_url:
                        await redis.delete(f"shortlink:{short_code}")
                        await redis.delete(f"longlink:{original_url.decode()}")

                await db.commit()

            except Exception as e:

                await db.rollback()  # ОТКАТ всех изменений в случае ошибки

        await asyncio.sleep(period)  