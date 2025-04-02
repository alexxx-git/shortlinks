API Documentation: URL Shortener Service
Base URL

http://your-domain.com/api/v1
Authentication

Все защищенные endpoints требуют JWT токена в заголовке:
Copy

Authorization: Bearer <your_token>

1. Authentication Endpoints
1.1 Register New User

Endpoint: POST /register
Description: Регистрация нового пользователя
Request:
json
Copy

{
  "username": "string",
  "email": "string",
  "password": "string"
}

Response:
json
Copy

{
  "message": "Регистрация успешна",
  "username": "string"
}

1.2 Login

Endpoint: POST /token
Description: Получение JWT токена
Request:
json
Copy

{
  "username": "string",
  "password": "string"
}

Response:
json
Copy

{
  "access_token": "string",
  "token_type": "bearer"
}

1.3 Logout

Endpoint: GET /logout
Description: Выход из системы (удаление cookie)
Response: Redirect to home page
2. URL Shortening Endpoints
2.1 Create Short Link

Endpoint: POST /links/shorten
Description: Создание короткой ссылки
Request:
json
Copy

{
  "original_url": "string",
  "customAlias": "string (optional)"
}

Response:
json
Copy

{
  "short_url": "string",
  "original_url": "string",
  "custom_alias": "string"
}

2.2 Redirect by Short Code

Endpoint: GET /links/{short_code}
Description: Перенаправление по короткой ссылке
Response: 302 Redirect to original URL
2.3 Update Short Link

Endpoint: PUT /links/{short_code}
Description: Обновление оригинального URL для короткой ссылки
Request:
json
Copy

{
  "new_url": "string"
}

Response:
json
Copy

{
  "short_code": "string",
  "new_url": "string",
  "created_at": "datetime"
}

2.4 Delete Short Link

Endpoint: DELETE /links/{short_code}
Description: Удаление короткой ссылки
Response:
json
Copy

{
  "message": "Link and visits successfully archived and deleted."
}

3. Analytics Endpoints
3.1 Get Link Stats

Endpoint: GET /links/{short_code}/stats
Description: Получение статистики по короткой ссылке
Response:
json
Copy

{
  "original_url": "string",
  "created_at": "datetime",
  "visit_count": "integer",
  "last_access_at": "datetime"
}

3.2 Search Short Link

Endpoint: GET /links/search
Description: Поиск короткой ссылки по оригинальному URL
Parameters:
Copy

?original_url=<url_encoded_string>

Response:
json
Copy

{
  "short_code": "string",
  "original_url": "string"
}

4. User Endpoints
4.1 Get Current User

Endpoint: GET /users/me
Description: Получение информации о текущем пользователе
Response:
json
Copy

{
  "username": "string"
}

Примеры запросов
Пример 1: Создание короткой ссылки
bash
Copy

curl -X POST "http://localhost:8000/links/shorten" \
-H "Authorization: Bearer your_jwt_token" \
-H "Content-Type: application/json" \
-d '{"original_url": "https://example.com/very/long/url"}'

Пример 2: Получение статистики
bash
Copy

curl -X GET "http://localhost:8000/links/abc123/stats" \
-H "Authorization: Bearer your_jwt_token"

Пример 3: Поиск ссылки
bash
Copy

curl -X GET "http://localhost:8000/links/search?original_url=https%3A%2F%2Fexample.com%2Fvery%2Flong%2Furl" \
-H "Authorization: Bearer your_jwt_token"

Особенности реализации

    Кеширование: Используется Redis для кеширования:

        shortlink:<code> → оригинальный URL

        longlink:<url> → короткий код

    Архивация: Удаленные и просроченные ссылки перемещаются в архивные таблицы

    Аналитика: Для каждого перехода сохраняется:

        Время доступа

        IP-адрес

        Страна

        Тип устройства

        Реферер

    Фоновая задача: Раз в час проверяет и архивирует просроченные ссылки

    Геолокация: Используется GeoIP2 для определения страны по IP

Ошибки
Код	Сообщение	Описание
400	This alias is already taken	Пользовательский алиас уже занят
401	Incorrect username or password	Неверные учетные данные
403	Invalid token	Невалидный JWT токен
404	Short link not found	Ссылка не найдена
500	Internal server error	Ошибка сервера
Дополнительные функции

    Авто-удаление:

        Для авторизованных пользователей: через 30 дней

        Для гостей: через 10 дней

    Параметр expires_at:
    Можно указать в URL параметре точное время истечения:
    ?expires_at=2024-12-31T23:59:59

    Кодирование URL:
    Все URL кодируются/декодируются для безопасного хранения

Эта документация полностью покрывает функционал вашего API. Для интеграции можно использовать Swagger UI или Redoc, добавив соответствующие маршруты в FastAPI.
ты можешь все что сказа перевести в md ? или как то сохранить  например в pdf?

Вот полная документация в формате Markdown (.md), которую вы можете сохранить или конвертировать в PDF:
markdown
Copy

# API Documentation: URL Shortener Service

## Base URL
`http://your-domain.com/api/v1`

---

## 📌 Table of Contents
1. [Authentication](#-authentication-endpoints)
2. [URL Shortening](#-url-shortening-endpoints)
3. [Analytics](#-analytics-endpoints)
4. [User Management](#-user-endpoints)
5. [Examples](#-examples)
6. [Implementation Details](#-implementation-details)
7. [Error Codes](#-error-codes)

---

## 🔐 Authentication Endpoints

### Register New User
`POST /register`

**Request Body**:
```json
{
  "username": "string",
  "email": "string",
  "password": "string"
}

Response:
json
Copy

{
  "message": "Registration successful",
  "username": "string"
}

Login

POST /token

Request Body:
json
Copy

{
  "username": "string",
  "password": "string"
}

Response:
json
Copy

{
  "access_token": "jwt_token",
  "token_type": "bearer"
}

✂️ URL Shortening Endpoints
Create Short Link

POST /links/shorten

Request Body:
json
Copy

{
  "original_url": "https://example.com/very/long/url",
  "customAlias": "myalias (optional)"
}

Response:
json
Copy

{
  "short_url": "http://your-domain.com/links/abc123",
  "original_url": "https://example.com/very/long/url",
  "custom_alias": "abc123"
}

Redirect

GET /links/{short_code}
Redirects to original URL
📊 Analytics Endpoints
Get Link Statistics

GET /links/{short_code}/stats

Response:
json
Copy

{
  "original_url": "https://example.com",
  "created_at": "2023-01-01T00:00:00",
  "visit_count": 42,
  "last_access_at": "2023-06-15T14:30:00"
}

👤 User Endpoints
Get Current User

GET /users/me

Response:
json
Copy

{
  "username": "john_doe"
}

🧪 Example Requests
cURL Examples
bash
Copy

# Create short link
curl -X POST "http://localhost:8000/links/shorten" \
  -H "Authorization: Bearer your_token" \
  -d '{"original_url":"https://example.com"}'

# Get stats
curl -X GET "http://localhost:8000/links/abc123/stats" \
  -H "Authorization: Bearer your_token"

⚙️ Implementation Details
Caching System
mermaid
Copy

graph LR
  A[Short Code] -->|Redis| B(Original URL)
  B -->|TTL| C(30 days for users)
  B -->|TTL| D(10 days for guests)

Database Architecture
Table	Purpose
short_links	Active links
short_links_archive	Deleted/expired links
visits	Access logs
visits_archive	Archived access logs
🚨 Error Codes
Code	Description
400	Invalid request data
401	Unauthorized
404	Resource not found
500	Server error




Database Schema Documentation
📌 Таблицы базы данных
1. Пользователи (users)

Описание: Хранит информацию о зарегистрированных пользователях
Поле	Тип	Описание
id	Integer	Первичный ключ
username	String	Уникальное имя пользователя
email	String	Уникальный email
password	String	Хэшированный пароль

Связи:

    links: Связь с активными короткими ссылками пользователя

    archived_links: Связь с архивными короткими ссылками пользователя

2. Короткие ссылки (short_links)

Описание: Активные короткие ссылки
Поле	Тип	Описание
id	Integer	Первичный ключ
user_id	Integer	Внешний ключ к пользователю (может быть NULL для гостей)
short_code	String	Уникальный короткий код (индексируется)
original_url	String	Оригинальный URL
created_at	DateTime	Дата создания (по умолчанию текущее время)
expires_at	DateTime	Время истечения (если задано вручную)
last_access_at	DateTime	Время последнего доступа
auto_expires_at	DateTime	Автоматическое время истечения

Связи:

    user: Связь с владельцем-пользователем

    visits: Связь с визитами этой ссылки

3. Архив коротких ссылок (short_links_archive)

Описание: Удаленные или просроченные короткие ссылки
Поле	Тип	Описание
id	Integer	Первичный ключ
user_id	Integer	Внешний ключ к пользователю
short_code	String	Короткий код (индексируется)
original_url	String	Оригинальный URL
created_at	DateTime	Дата создания
expires_at	DateTime	Время истечения
last_access_at	DateTime	Время последнего доступа
auto_expires_at	DateTime	Автоматическое время истечения
archived_at	DateTime	Время архивации
archival_reason	String	Причина архивации

Связи:

    user: Связь с владельцем-пользователем

    visits_archive: Связь с архивными визитами

4. Визиты (visits)

Описание: Статистика переходов по коротким ссылкам
Поле	Тип	Описание
id	Integer	Первичный ключ
owner	Integer	ID пользователя (если известен)
timestamp	DateTime	Время визита (индексируется)
short_code	String	Внешний ключ к короткой ссылке
original_url	String	Оригинальный URL
domain_1st	String	Домен первого уровня (например "com")
domain_2nd	String	Домен второго уровня (например "example.com")
ip_address	String	IP-адрес посетителя
device_type	String	Тип устройства ("mobile"/"desktop")
country	String	Код страны (определяется по IP)
referer	String	Источник перехода

Связи:

    short_link: Связь с основной короткой ссылкой

5. Архив визитов (visit_archives)

Описание: Архивная статистика переходов
Поле	Тип	Описание
id	Integer	Первичный ключ
owner	Integer	ID пользователя
timestamp	DateTime	Время визита (индексируется)
short_code	String	Короткий код (индексируется)
original_url	String	Оригинальный URL
domain_1st	String	Домен первого уровня
domain_2nd	String	Домен второго уровня
ip_address	String	IP-адрес
device_type	String	Тип устройства
country	String	Код страны
referer	String	Источник перехода
archived_at	DateTime	Время архивации
archival_reason	String	Причина архивации

Связи:

    archived_link: Связь с архивной короткой ссылкой

🔗 Диаграмма связей
mermaid
Copy

erDiagram
    users ||--o{ short_links : "links"
    users ||--o{ short_links_archive : "archived_links"
    short_links ||--o{ visits : "visits"
    short_links_archive ||--o{ visit_archives : "visits_archive"
    
    users {
        int id PK
        string username
        string email
        string password
    }
    
    short_links {
        int id PK
        int user_id FK
        string short_code
        string original_url
        datetime created_at
        datetime expires_at
        datetime last_access_at
        datetime auto_expires_at
    }
    
    short_links_archive {
        int id PK
        int user_id FK
        string short_code
        string original_url
        datetime archived_at
        string archival_reason
    }
    
    visits {
        int id PK
        string short_code FK
        string ip_address
        string device_type
        string country
    }
    
    visit_archives {
        int id PK
        string short_code FK
        datetime archived_at
        string archival_reason
    }

📌 Ключевые особенности

    Разделение на активные и архивные данные:

        Активные ссылки → short_links

        Архивные ссылки → short_links_archive

        Активные визиты → visits

        Архивные визиты → visit_archives

    Индексация:

        Все short_code индексируются для быстрого поиска

        timestamp в визитах индексируется для аналитики

    Автоматическое удаление:

        Поле auto_expires_at определяет срок "жизни" ссылки

        Фоновая задача переносит устаревшие данные в архив

    Геоданные:

        Сохранение страны (country) и типа устройства (device_type)

        Аналитика по доменам (domain_1st, domain_2nd)