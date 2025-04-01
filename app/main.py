from fastapi import FastAPI, Depends, HTTPException, Request, Form, Cookie, status, Query, Body,  Header
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from database import  get_db, engine
from models import User, ShortLink, ShortLinkArchive,Visit,VisitArchive
from schemas import LinkRequest, ShortLinkUpdateModel
from auth import authenticate_user, hash_password, verify_password
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, LINK_EXPIRE_TIME_IN_MINUTES, REDIS_TTL
from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles
from redis_cache import get_redis, redis_dependency
from redis.asyncio import Redis
import hashlib
import random
import string
from pydantic import HttpUrl
import json
from typing import Optional
from fastapi import Request
from urllib.parse import urlparse, parse_qs, urlencode, unquote, quote
import geoip2.database


def random_salt():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))


def generate_short_code(original_url: HttpUrl) -> str:
    original_url_str = str(original_url)  # Преобразуем HttpUrl в строку
    hash_value = hashlib.sha256((original_url_str + random_salt()).encode()).hexdigest()
    return hash_value[:8]  # Обрезаем до 8 символов

app = FastAPI()
templates = Jinja2Templates(directory="templates")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@asynccontextmanager
async def lifespan(app: FastAPI):
  
    # Подключение к Redis (с await!)
    get_redis()
  
    # Инициализация БД
    async with engine.begin() as conn:
        await conn.run_sync(User.metadata.create_all)
    
    yield  # Здесь приложение работает
    # await close_redis()
    # # Закрытие соединения с Redis
    # if redis:
    #     await close_redis(redis)

app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="templates/static"), name="static")



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

from fastapi.responses import JSONResponse


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
    # 🛠️ Извлекаем expires_at и очищенный URL
    cleaned_url, expires_at_query = extract_expires_at(link_request.original_url)

    short_code = link_request.customAlias

    # 🔍 Если пользователь не авторизован и не указан параметр expire, проверяем наличие ссылки в Redis
    if not user_id and not expires_at_query:
        # Проверяем наличие короткого кода для данного длинного URL
        redis_key = f"longlink:{quote(cleaned_url)}"  # Кодируем длинный URL
        existing_short_code = await redis.get(redis_key)

        if existing_short_code:
            short_code = existing_short_code  # Уже строка, decode() не нужен!
            await redis.expire(redis_key, REDIS_TTL)
            await redis.expire(f"shortlink:{short_code}", REDIS_TTL)
            
            host = str(request.base_url).rstrip("/")
            return {
                "short_url": f"{host}/links/{short_code}",
                "original_url": cleaned_url,
                "custom_alias": short_code,
                "from_cache": True
            }

    # 🔍 Проверяем уникальность alias, если он задан
    if short_code:
        redis_key = f"shortlink:{quote(short_code)}"  # Кодируем короткий код

        if await redis.exists(redis_key):
            raise HTTPException(status_code=400, detail="This alias is already taken. Please choose another.")

        query = select(ShortLink).where(ShortLink.short_code == short_code)
        result = await db.execute(query)
        if result.scalars().first():
            raise HTTPException(status_code=400, detail="This alias is already taken. Please choose another.")

    else:
        # 🆕 Генерируем короткий код
        while True:
            short_code = generate_short_code(cleaned_url)
            redis_key = f"shortlink:{quote(short_code)}"  # Кодируем короткий код

            if await redis.exists(redis_key):
                continue

            query = select(ShortLink).where(ShortLink.short_code == short_code)
            result = await db.execute(query)
            if result.scalars().first():
                continue

            break  # Нашли уникальный short_code

    # Кодируем URL перед сохранением в Redis
    encoded_url = quote(cleaned_url)  # Кодируем оригинальный URL

    # 🕒 Вычисляем TTL для Redis
    if expires_at_query:
        ttl = min((expires_at_query - datetime.now()).total_seconds(), REDIS_TTL)
    else:
        ttl = REDIS_TTL

    # Сохраняем в Redis обе пары (короткий → длинный и длинный → короткий)
    await redis.set(f"shortlink:{quote(short_code)}", encoded_url, ex=int(ttl))  # Кодируем и короткий, и длинный URL
    await redis.set(f"longlink:{encoded_url}", quote(short_code), ex=int(ttl))  # Кодируем длинный URL и короткий код

    # Вычисляем время истечения ссылки для базы данных
    if expires_at_query:
        auto_expires = None  # Если задан `expires_at`, авто-удаление не нужно
        expires_at = expires_at_query
    else:
        auto_expires = datetime.now() + timedelta(days=30) if user_id else datetime.now() + timedelta(days=10)
        expires_at = None

    # Сохраняем в базе данных
    new_link = ShortLink(
        short_code=short_code,
        original_url=cleaned_url,  # Очищенный URL без `expires_at`
        created_at=datetime.now(),
        expires_at=expires_at,
        user_id=user_id,
        auto_expires_at=auto_expires
    )
    db.add(new_link)
    await db.commit()

    # 📎 Генерируем короткий URL
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
reader = geoip2.database.Reader('GeoLite2-Country.mmdb')

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

@app.get("/links/{short_code}")
async def redirect_to_original_link(
    short_code: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(redis_dependency),
):
    print(short_code)
    redis_key = f"shortlink:{short_code}"
    user_cache_key = f"short_ui:{short_code}"  # Кэш user_id
    print(user_cache_key)

    # Проверяем кэш user_id
    user_id = await redis.get(user_cache_key)
    if user_id is None:
        # Если user_id нет в кэше, ищем в БД
        query = select(ShortLink.user_id).where(ShortLink.short_code == short_code)
        result = await db.execute(query)
        user_id = result.scalar()

        # Если user_id не найден, считаем, что это гость (None)
        if user_id is None:
            user_id = None  # Гость

        # Сохраняем user_id в кэш
        await redis.set(user_cache_key, str(user_id) if user_id is not None else "guest", ex=REDIS_TTL)
    else:
        user_id = None if user_id == "guest" else int(user_id)

    print(f"user_id: {user_id}")

    # Проверяем кэш ссылки
    encoded_url = await redis.get(redis_key)
    print(f"encoded_url: {encoded_url}")

    if encoded_url:
        original_url = decode_url(encoded_url)
        await redis.expire(redis_key, REDIS_TTL)
        await redis.expire(f"longlink:{encoded_url}", REDIS_TTL)
    else:
        # Если в Redis нет, ищем в БД
        print(f"seeking in db: {short_code}")
        query = select(ShortLink).where(ShortLink.short_code == short_code)
        result = await db.execute(query)
        short_link = result.scalars().first()

        if not short_link:
            return RedirectResponse("https://www.google.com/")  # Редирект на Google

        original_url = short_link.original_url
        await redis.set(redis_key, encode_url(original_url), ex=REDIS_TTL)

    # Извлекаем IP-адрес пользователя
    ip_address = request.client.host if request.client else "unknown"

    # Определяем страну по IP
    country = get_country_by_ip(ip_address)

    # Определяем тип устройства
    user_agent = request.headers.get("User-Agent", "").lower()
    device_type = "mobile" if "mobile" in user_agent else "desktop"

    # Парсим домены через urlparse
    domain_1st, domain_2nd = parse_domains(original_url)

    # Сохраняем посещение в БД
    print('Запись в БД')
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
    await db.commit()

    return RedirectResponse(original_url)



@app.delete("/links/{short_code}")
async def delete_short_link(
    short_code: str,
    user_id: int = Depends(get_user_from_token),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(redis_dependency),
):
    print(f"Получен запрос на удаление ссылки с кодом: {short_code} от пользователя с ID: {user_id}")
    
    if user_id is None:
        print("Ошибка: Попытка удалить ссылку неавторизованным пользователем.")
        return {"error": "Unauthorized: Guest users cannot delete links."}

    try:
        # Проверяем, существует ли короткая ссылка в БД и принадлежит ли она пользователю
        query = select(ShortLink).where(ShortLink.short_code == short_code, ShortLink.user_id == user_id)
        result = await db.execute(query)
        short_link = result.scalars().first()

        if not short_link:
            print(f"Ошибка: Ссылка с кодом {short_code} не найдена или не принадлежит пользователю {user_id}.")
            return {"error": "Link not found or you do not have permission to delete it."}

        print(f"Ссылка с кодом {short_code} найдена и принадлежит пользователю {user_id}.")

        # Переносим ссылку в архив
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
        print(f"Ссылка с кодом {short_code} перенесена в архив.")

        # Переносим все визиты в архив
        query_visits = select(Visit).where(Visit.short_code == short_code)
        result_visits = await db.execute(query_visits)
        visits = result_visits.scalars().all()

        if visits:
            print(f"Найдено {len(visits)} визитов для ссылки {short_code}. Переносим их в архив.")
            
            # Удаляем визиты после архивации
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
                await db.delete(visit)  # Удаляем оригинальный визит

        else:
            print(f"Визитов для ссылки {short_code} не найдено.")

        # Удаляем оригинальную запись из таблицы ShortLink
        await db.delete(short_link)
        print(f"Оригинальная запись ссылки с кодом {short_code} удалена из таблицы ShortLink.")

        # Обновляем кэш в Redis
        await redis.delete(f"shortlink:{short_code}")
        await redis.delete(f"short_ui:{short_code}")
        print(f"Кэш для ссылки с кодом {short_code} удален из Redis.")

        # Сохраняем изменения в базе данных
        await db.commit()
        print(f"Изменения сохранены в базе данных. Ссылка с кодом {short_code} успешно удалена.")
        
    except Exception as e:
        # В случае ошибки откатываем изменения
        print(f"Произошла ошибка: {e}")
        await db.rollback()
        return {"error": f"An error occurred while deleting the link: {str(e)}"}

    return {"message": "Link and visits successfully archived and deleted."}




@app.put("/links/{short_code}")
async def update_short_link(
    short_code: str,
    new_url: str,  # Новый URL для короткой ссылки
    redis: Redis = Depends(redis_dependency),  # Зависимость для Redis
    db: AsyncSession = Depends(get_db),  # Зависимость для базы данных
):
    # Проверка корректности нового URL
    if not re.match(r"^https?://", new_url):
        raise HTTPException(status_code=400, detail="Некорректный URL")

    # Кодируем новый URL для безопасного хранения в Redis
    encoded_url = encode_url(new_url)

    # Находим самую свежую запись с данным short_code
    query = select(ShortLink).where(ShortLink.short_code == short_code).order_by(ShortLink.updated_at.desc())
    result = await db.execute(query)
    short_link = result.scalars().first()

    if not short_link:
        raise HTTPException(status_code=404, detail="Short link not found")

    # Обновляем URL в базе данных
    short_link.original_url = new_url
    await db.commit()  # Сохраняем изменения в базе данных

    # Удаляем старый кэш из Redis (для старого URL)
    old_encoded_url = encode_url(short_link.original_url)
    await redis.delete(f"longlink:{old_encoded_url}")

    # Обновляем кэш в Redis для нового URL
    await redis.delete(f"shortlink:{short_code}")  # Удаляем старый кэш
    await redis.set(f"shortlink:{short_code}", new_url)  # Добавляем новый кэш

    # Кешируем новый длинный URL
    await redis.set(f"longlink:{encoded_url}", short_code)

    return {"short_code": short_code, "new_url": new_url}


@app.get("/links/search")
async def search_short_link(
    original_url: str,
    redis: Redis = Depends(redis_dependency),
    db: AsyncSession = Depends(get_db),
):
    print(f"Поиск короткой ссылки для оригинального URL: {original_url}")

    # Валидация URL
    if not re.match(r"^https?://", original_url):
        raise HTTPException(status_code=400, detail="Некорректный URL")

    # Кодируем URL для Redis
    encoded_url = encode_url(original_url)

    # 1. Ищем в Redis
    cached_short_code = await redis.get(f"longlink:{encoded_url}")
    if cached_short_code:
        short_code = decode_url(cached_short_code.decode())  # Декодируем из Redis
        print(f"Найдена короткая ссылка в Redis: {short_code}")
        return {"short_code": short_code, "original_url": original_url}

    # 2. Если в Redis нет, ищем в БД (самую свежую)
    query = (
        select(ShortLink)
        .where(ShortLink.original_url == original_url)
        .order_by(ShortLink.created_at.desc())  # Берем самую свежую
    )
    result = await db.execute(query)
    short_link = result.scalars().first()

    if not short_link:
        raise HTTPException(status_code=404, detail="Short link not found for the provided URL")

    # 3. Кешируем в Redis (кодируем short_code!)
    await redis.set(f"longlink:{encoded_url}", encode_url(short_link.short_code))

    print(f"Найдена короткая ссылка в базе: {short_link.short_code}")

    return {"short_code": short_link.short_code, "original_url": short_link.original_url}
