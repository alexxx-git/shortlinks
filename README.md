### 🔗 Сервис сокращения ссылок  SUS:ShortURL Service

Этот проект представляет собой сервис для сокращения ссылок с возможностью отслеживания посещений и управления архивированием данных.  

---

### 🚀 Основные возможности:

✅ **Регистрация пользователей** – учетные записи с уникальными логинами и паролями.  
✅ **Создание коротких ссылок** – преобразование длинных URL в короткие коды.  
✅ **Отслеживание посещений** – сбор статистики по кликам, включая IP, страну, устройство и источник перехода.  
✅ **Архивация ссылок** – перемещение устаревших или удаленных ссылок и визитов в архив без полного удаления данных.  
✅ **Использование PostgreSQL и Redis** – основное хранилище в PostgreSQL, кэширование данных через Redis.  

Проект может быть полезен для **аналитики, маркетинга** и удобного управления ссылками. 🚀  

---

### 🛠 Установка:

```bash
# 1. Клонировать репозиторий
git clone https://github.com/alexxx-git/shortlinks.git
cd your-repo  

# 2. Запустить проект с помощью Docker  
docker-compose up -d --build
```


После успешного запуска сервис будет доступен по адресу: http://localhost:8000





<h3 style="color: #4CAF50;">GET /</h3>

<h4 style="font-weight: bold; color: #2196F3;">Описание</h4>
<p>Этот эндпоинт возвращает главную страницу веб-приложения. Если в cookies присутствует токен авторизации, система пытается извлечь из него имя пользователя.</p>

<ul>
  <li>При наличии корректного JWT-токена в cookies отображается имя пользователя.</li>
  <li>Если токен отсутствует или недействителен, страница загружается без имени пользователя.</li>
  <li>Используется шаблон <code>index.html</code> для рендеринга.</li>
</ul>

<h4 style="font-weight: bold; color: #2196F3;">Запрос</h4>
<ul>
  <li><span style="font-weight: bold; color: #00796B;">Метод</span>: <span style="color: #009688;">GET</span></li>
  <li><span style="font-weight: bold; color: #00796B;">URL</span>: <code style="color: #009688;">/</code></li>
  <li><span style="font-weight: bold; color: #00796B;">Cookies</span>: 
    <ul>
      <li><span style="font-weight: bold; color: #00796B;">token</span>: <code style="color: #009688;">string</code>, необязательный JWT-токен пользователя.</li>
    </ul>
  </li>
</ul>

<h4 style="font-weight: bold; color: #2196F3;">Ответ</h4>
<ul>
  <li><span style="font-weight: bold; color: #388E3C;">Статус 200</span>: Успешный рендеринг страницы.
    <pre><code style="color: #FF9800;">&lt;HTML страницы index.html&gt;</code></pre>
  </li>
</ul>





<h3 style="color: #4CAF50;">GET /users/me</h3>
<h4 style="font-weight: bold; color: #2196F3;">Описание</h4>
<p>Этот эндпоинт используется для получения информации о текущем пользователе на основе переданного токена. Он декодирует JWT-токен и извлекает из него имя пользователя (если токен действителен).</p>
<ul>
  <li>Токен передается либо в строке запроса, например: <code style="color: #FF5722;">/users/me?token=&lt;JWT&gt;</code>, либо в заголовке <code style="color: #FF5722;">Authorization</code> в формате: <span style="color: #FF9800;">Authorization: Bearer &lt;JWT&gt;</span>.</li>
  <li>Токен должен быть действительным. Если токен повреждён или с истёкшим сроком действия, ответ будет содержать ошибку.</li>
</ul>
<h4 style="font-weight: bold; color: #2196F3;">Запрос</h4>
<ul>
  <li><span style="font-weight: bold; color: #00796B;">Метод</span>: <span style="color: #009688;">GET</span></li>
  <li><span style="font-weight: bold; color: #00796B;">URL</span>: <code style="color: #009688;">/users/me</code></li>
  <li><span style="font-weight: bold; color: #00796B;">Параметры запроса</span>: <span style="color: #FF5722;"><b>token</b></span> (строка): JWT-токен, передаваемый через заголовок <code style="color: #FF5722;">Authorization</code> или в качестве параметра строки запроса.</li>
</ul>
<h4 style="font-weight: bold; color: #2196F3;">Ответ</h4>
<ul>
  <li><span style="font-weight: bold; color: #388E3C;">Статус 200</span>: Успешный запрос, возвращает имя пользователя.
    <pre><code style="color: #FF9800;">{"username": "example_user"}</code></pre>
  </li>
  <li><span style="font-weight: bold; color: #D32F2F;">Статус 403</span>: Ошибка авторизации. Токен недействителен или отсутствует.
    <pre><code style="color: #FF9800;">{"detail": "Неверный токен"}</code></pre>
  </li>
</ul>



<h3 style="color: #4CAF50;">POST /register</h3>

<h4 style="font-weight: bold; color: #2196F3;">Описание</h4>
<p>Этот эндпоинт позволяет зарегистрировать нового пользователя. Он проверяет, занят ли выбранный username или email, и если они уже существуют, возвращает ошибку. В случае успешной регистрации возвращается сообщение с подтверждением.</p>

<ul>
  <li>Проверяется наличие пользователя с таким же <code style="color: #FF5722;">username</code> или <code style="color: #FF5722;">email</code> в базе данных.</li>
  <li>Если такой пользователь найден, возвращается ошибка с соответствующим сообщением ("Имя пользователя уже занято" или "Email уже зарегистрирован").</li>
  <li>Если пользователь уникален, создаётся новый аккаунт с зашифрованным паролем и сохраняется в базе данных.</li>
  <li>После успешной регистрации возвращается сообщение о успешной регистрации с именем пользователя.</li>
</ul>

<h4 style="font-weight: bold; color: #2196F3;">Запрос</h4>
<ul>
  <li><span style="font-weight: bold; color: #00796B;">Метод</span>: <span style="color: #009688;">POST</span></li>
  <li><span style="font-weight: bold; color: #00796B;">URL</span>: <code style="color: #009688;">/register</code></li>
  <li><span style="font-weight: bold; color: #00796B;">Тело запроса</span>: Форма с параметрами:
    <ul>
      <li><span style="font-weight: bold; color: #00796B;">username</span>: Имя пользователя (строка)</li>
      <li><span style="font-weight: bold; color: #00796B;">email</span>: Адрес электронной почты (строка)</li>
      <li><span style="font-weight: bold; color: #00796B;">password</span>: Пароль пользователя (строка)</li>
    </ul>
  </li>
</ul>

<h4 style="font-weight: bold; color: #2196F3;">Ответ</h4>
<ul>
  <li><span style="font-weight: bold; color: #388E3C;">Статус 200</span>: Успешная регистрация.
    <pre><code style="color: #FF9800;">{"message": "Регистрация успешна", "username": "username"}</code></pre>
  </li>
  <li><span style="font-weight: bold; color: #D32F2F;">Статус 400</span>: Ошибка при регистрации. Имя пользователя или email уже заняты.
    <pre><code style="color: #FF9800;">{"detail": "Имя пользователя уже занято"}</code></pre>
    или
    <pre><code style="color: #FF9800;">{"detail": "Email уже зарегистрирован"}</code></pre>
  </li>
  <li><span style="font-weight: bold; color: #D32F2F;">Статус 500</span>: Внутренняя ошибка сервера.
    <pre><code style="color: #FF9800;">{"detail": "Внутренняя ошибка сервера"}</code></pre>
  </li>
</ul>



<h3 style="color: #4CAF50;">POST /token</h3>

<h4 style="font-weight: bold; color: #2196F3;">Описание</h4>
<p>Этот эндпоинт позволяет пользователям аутентифицироваться с помощью имени пользователя и пароля, чтобы получить токен доступа. 
Токен используется для авторизации на защищённых эндпоинтах системы. Токен имеет срок действия, после чего его нужно будет обновить или запросить заново.</p>

<ul>
  <li>Пользователь предоставляет имя пользователя и пароль через форму.</li>
  <li>Система проверяет наличие пользователя в базе данных и соответствие пароля.</li>
  <li>Если данные верны, генерируется токен доступа с указанным сроком действия.</li>
  <li>Токен возвращается в формате JSON.</li>
</ul>

<h4 style="font-weight: bold; color: #2196F3;">Запрос</h4>
<ul>
  <li><span style="font-weight: bold; color: #00796B;">Метод</span>: <span style="color: #009688;">POST</span></li>
  <li><span style="font-weight: bold; color: #00796B;">URL</span>: <code style="color: #009688;">/token</code></li>
  <li><span style="font-weight: bold; color: #00796B;">Тело запроса</span>: Форма с параметрами:
    <pre><code style="color: #FF9800;">{
  "username": "user123",
  "password": "password123"
}</code></pre>
  </li>
</ul>

<h4 style="font-weight: bold; color: #2196F3;">Ответ</h4>
<ul>
  <li><span style="font-weight: bold; color: #388E3C;">Статус 200</span>: Успешная аутентификация, возвращает токен доступа.
    <pre><code style="color: #FF9800;">{
  "access_token": "your_token_here",
  "token_type": "bearer"
}</code></pre>
  </li>
  <li><span style="font-weight: bold; color: #D32F2F;">Статус 401</span>: Ошибка авторизации, неверное имя пользователя или пароль.
    <pre><code style="color: #FF9800;">{
  "detail": "Incorrect username or password"
}</code></pre>
  </li>
</ul>


<h3 style="color: #4CAF50;">GET /logout</h3>

<h4 style="font-weight: bold; color: #2196F3;">Описание</h4>
<p>Этот эндпоинт позволяет пользователю выйти из системы. Он удаляет токен авторизации, хранящийся в куки, и перенаправляет пользователя на главную страницу.</p>

<ul>
  <li>После выхода из системы, токен авторизации удаляется из куки.</li>
  <li>Пользователь перенаправляется на главную страницу (или другую, в зависимости от конфигурации).</li>
</ul>

<h4 style="font-weight: bold; color: #2196F3;">Запрос</h4>
<ul>
  <li><span style="font-weight: bold; color: #00796B;">Метод</span>: <span style="color: #009688;">GET</span></li>
  <li><span style="font-weight: bold; color: #00796B;">URL</span>: <code style="color: #009688;">/logout</code></li>
  <li><span style="font-weight: bold; color: #00796B;">Тело запроса</span>: Не требуется.</li>
</ul>

<h4 style="font-weight: bold; color: #2196F3;">Ответ</h4>
<ul>
  <li><span style="font-weight: bold; color: #388E3C;">Статус 200</span>: Успешный запрос, токен удалён из куки, пользователь перенаправлен на главную страницу.
    <pre><code style="color: #FF9800;">{
  "message": "Successfully logged out"
}</code></pre>
  </li>
</ul>




<h3 style="color: #4CAF50;">POST /links/shorten</h3>

<h4 style="font-weight: bold; color: #2196F3;">Описание</h4>
<p>Этот эндпоинт позволяет сократить длинную ссылку и получить уникальный короткий код. 
Если пользователь авторизован, ссылка сохраняется в его профиле. 
Анонимные пользователи могут получить временную ссылку, которая будет кэшироваться в Redis.</p>

<ul>
  <li>Если пользователь не зарегистрирован и не передаёт время истечения, сервис проверяет кеш для предотвращения дублирования коротких ссылок. Также осуществляется проверка в базе данных, чтобы убедиться, что ссылка не была ранее создана для незарегистрированных пользователей.</li>
  <li>Если передан <code style="color: #FF5722;">customAlias</code>, проверяется его уникальность.</li>
  <li>Если <code style="color: #FF5722;">customAlias</code> не указан, генерируется случайный короткий код.</li>
  <li>Срок хранения ссылки зависит от наличия авторизации и переданного времени истечения.</li>
  <li>Для авторизованных пользователей срок хранения ссылки составляет 30 дней.</li>
  <li>Для анонимных пользователей срок хранения ссылки составляет 10 дней.</li>
</ul>

<h4 style="font-weight: bold; color: #2196F3;">Запрос</h4>
<ul>
  <li><span style="font-weight: bold; color: #00796B;">Метод</span>: <span style="color: #009688;">POST</span></li>
  <li><span style="font-weight: bold; color: #00796B;">URL</span>: <code style="color: #009688;">/links/shorten</code></li>
  <li><span style="font-weight: bold; color: #00796B;">Тело запроса</span>: JSON-объект с параметрами:
    <pre><code style="color: #FF9800;">{"original_url": "https://example.com", "customAlias": "myalias"}</code></pre>
  </li>
</ul>

<h4 style="font-weight: bold; color: #2196F3;">Ответ</h4>
<ul>
  <li><span style="font-weight: bold; color: #388E3C;">Статус 200</span>: Успешный запрос, возвращает сокращённую ссылку.
    <pre><code style="color: #FF9800;">{"short_url": "https://short.ly/abc123", "original_url": "https://example.com", "custom_alias": "abc123"}</code></pre>
  </li>
  <li><span style="font-weight: bold; color: #D32F2F;">Статус 400</span>: Ошибка валидации или занятый alias.
    <pre><code style="color: #FF9800;">{"detail": "This alias is already taken. Please choose another."}</code></pre>
  </li>
</ul>


<h3 style="color: #4CAF50;">GET /links/{short_code}</h3>

<h4 style="font-weight: bold; color: #2196F3;">Описание</h4>
<p>Этот эндпоинт позволяет перенаправить пользователя по короткому коду на оригинальную ссылку. 
Он проверяет кэш (Redis) для быстрого ответа и, если ссылка не найдена, извлекает её из базы данных. 
Также собирается информация о визите пользователя, включая его устройство, страну и IP-адрес.</p>

<ul>
  <li>Если ссылка найдена в Redis, она используется для редиректа, и время жизни кэша обновляется.</li>
  <li>Если ссылка не найдена в кэше, происходит её извлечение из базы данных.</li>
  <li>Если короткий код не существует в базе данных, происходит редирект на страницу Google.</li>
  <li>Собирается информация о визите (IP-адрес, устройство, страна) и сохраняется в базе данных для дальнейшего анализа.</li>
  <li>После редиректа обновляется поле <code style="color: #FF5722;">last_access_at</code> для соответствующей ссылки, чтобы отслеживать время последнего доступа.</li>
</ul>

<h4 style="font-weight: bold; color: #2196F3;">Запрос</h4>
<ul>
  <li><span style="font-weight: bold; color: #00796B;">Метод</span>: <span style="color: #009688;">GET</span></li>
  <li><span style="font-weight: bold; color: #00796B;">URL</span>: <code style="color: #009688;">/links/{short_code}</code></li>
  <li><span style="font-weight: bold; color: #00796B;">Параметры пути</span>: 
    <ul>
      <li><span style="font-weight: bold; color: #00796B;">short_code</span>: Уникальный короткий код ссылки, которая будет использована для редиректа.</li>
    </ul>
  </li>
  <li><span style="font-weight: bold; color: #00796B;">Заголовки запроса</span>: 
    <ul>
      <li><span style="font-weight: bold; color: #00796B;">User-Agent</span>: Заголовок, содержащий информацию об устройстве клиента.</li>
      <li><span style="font-weight: bold; color: #00796B;">Referer</span>: Заголовок, содержащий информацию о предыдущей странице (если доступно).</li>
    </ul>
  </li>
</ul>

<h4 style="font-weight: bold; color: #2196F3;">Ответ</h4>
<ul>
  <li><span style="font-weight: bold; color: #388E3C;">Статус 200</span>: Успешный редирект на оригинальную ссылку.
    <pre><code style="color: #FF9800;">Перенаправление на оригинальную ссылку.</code></pre>
  </li>
  <li><span style="font-weight: bold; color: #D32F2F;">Статус 404</span>: Если короткий код не существует, происходит редирект на Google.
    <pre><code style="color: #FF9800;">Перенаправление на https://www.google.com/</code></pre>
  </li>
</ul>






<h3 style="color: #4CAF50;">DELETE /links/{short_code}</h3>

<h4 style="font-weight: bold; color: #2196F3;">Описание</h4>
<p>Этот эндпоинт позволяет авторизованному пользователю удалить свою короткую ссылку. При этом все данные о ссылке и её визитах сохраняются в архив, а сама ссылка удаляется из базы данных и кэша Redis.</p>

<ul>
  <li>Пользователь должен быть авторизован для удаления ссылки.</li>
  <li>Если ссылка не существует или не принадлежит пользователю, возвращается ошибка.</li>
  <li>После удаления, ссылка и её визиты архивируются и удаляются из базы данных и кэша Redis.</li>
  <li>Если для ссылки были найдены визиты, они также сохраняются в архив.</li>
</ul>

<h4 style="font-weight: bold; color: #2196F3;">Запрос</h4>
<ul>
  <li><span style="font-weight: bold; color: #00796B;">Метод</span>: <span style="color: #009688;">DELETE</span></li>
  <li><span style="font-weight: bold; color: #00796B;">URL</span>: <code style="color: #009688;">/links/{short_code}</code></li>
  <li><span style="font-weight: bold; color: #00796B;">Тело запроса</span>: Не требуется. Параметр <code style="color: #009688;">short_code</code> передаётся в URL.</li>
</ul>

<h4 style="font-weight: bold; color: #2196F3;">Ответ</h4>
<ul>
  <li><span style="font-weight: bold; color: #388E3C;">Статус 200</span>: Ссылка успешно удалена, данные о ссылке и визитах архивированы.
    <pre><code style="color: #FF9800;">{"Сообщение": "Данные ссылки и посещений заархивированы и стёрты."}</code></pre>
  </li>
  <li><span style="font-weight: bold; color: #F44336;">Статус 401</span>: Ошибка авторизации, пользователь не авторизован.
    <pre><code style="color: #FF9800;">{"Ошибка": "Попытка удалить ссылку неавторизованным пользователем."}</code></pre>
  </li>
  <li><span style="font-weight: bold; color: #F44336;">Статус 404</span>: Ссылка не найдена или не принадлежит пользователю.
    <pre><code style="color: #FF9800;">{"Ошибка": "Ссылка не найдена или у вас нет прав на ее удаление."}</code></pre>
  </li>
  <li><span style="font-weight: bold; color: #F44336;">Статус 500</span>: Ошибка при удалении ссылки или визитов.
    <pre><code style="color: #FF9800;">{"error": "Произошла ошибка при удалении ссылки: <описание ошибки>"}</code></pre>
  </li>
</ul>





<h3 style="color: #4CAF50;">PUT /links/{short_code}</h3>

<h4 style="font-weight: bold; color: #2196F3;">Описание</h4>
<p>Этот эндпоинт обновляет URL для короткой ссылки. Пользователь может изменить оригинальный URL своей короткой ссылки. В ответ возвращаются обновленные данные с новой ссылкой, временем её создания и временем автозавершения. Также происходит очистка старого кэша и обновление кэша в Redis.</p>

<ul>
  <li>Пользователь может обновить URL только для своих коротких ссылок.</li>
  <li>После обновления ссылки, кэш Redis очищается от старых значений и сохраняется новый URL с его сроком действия.</li>
  <li>После обновления ссылки, её время создания и время автозавершения (если предусмотрено) обновляются.</li>
  <li>В случае ошибки, если ссылка не найдена или пользователь не является её владельцем, возвращается ошибка с соответствующим сообщением.</li>
</ul>

<h4 style="font-weight: bold; color: #2196F3;">Запрос</h4>
<ul>
  <li><span style="font-weight: bold; color: #00796B;">Метод</span>: <span style="color: #009688;">PUT</span></li>
  <li><span style="font-weight: bold; color: #00796B;">URL</span>: <code style="color: #009688;">/links/{short_code}</code></li>
  <li><span style="font-weight: bold; color: #00796B;">Тело запроса</span>: <pre><code style="color: #009688;">{
  "new_url": "http://newurl.com"
}</code></pre></li>
</ul>

<h4 style="font-weight: bold; color: #2196F3;">Ответ</h4>
<ul>
  <li><span style="font-weight: bold; color: #388E3C;">Статус 200</span>: Успешное обновление ссылки.
    <pre><code style="color: #FF9800;">{
  "short_code": "abc123",
  "new_url": "http://newurl.com",
  "created_at": "2025-04-03T12:00:00",
  "auto_expires_at": "2025-04-10T12:00:00",
  "message": "Ссылка успешно обновлена"
}</code></pre>
  </li>
  <li><span style="font-weight: bold; color: #F44336;">Статус 400</span>: Некорректный URL.
    <pre><code style="color: #FF9800;">{
  "detail": "Некорректный URL"
}</code></pre>
  </li>
  <li><span style="font-weight: bold; color: #F44336;">Статус 404</span>: Ссылка не найдена или у пользователя нет прав на её изменение.
    <pre><code style="color: #FF9800;">{
  "detail": "Ссылка не найдена или у вас нет прав на её изменение"
}</code></pre>
  </li>
</ul>




<h3 style="color: #4CAF50;">GET /links/{short_code}/stats</h3>

<h4 style="font-weight: bold; color: #2196F3;">Описание</h4>
<p>Этот эндпоинт возвращает статистику для короткой ссылки, включая оригинальный URL, количество визитов, дату создания и дату последнего доступа. Статистика может быть полезна для анализа использования ссылки.</p>

<ul>
  <li>Возвращается количество визитов для указанной короткой ссылки.</li>
  <li>Возвращается оригинальный URL, дата создания и дата последнего доступа.</li>
  <li>Если ссылка не найдена, возвращается ошибка с кодом 404.</li>
</ul>

<h4 style="font-weight: bold; color: #2196F3;">Запрос</h4>
<ul>
  <li><span style="font-weight: bold; color: #00796B;">Метод</span>: <span style="color: #009688;">GET</span></li>
  <li><span style="font-weight: bold; color: #00796B;">URL</span>: <code style="color: #009688;">/links/{short_code}/stats</code></li>
  <li><span style="font-weight: bold; color: #00796B;">Тело запроса</span>: Не требуется.</li>
</ul>

<h4 style="font-weight: bold; color: #2196F3;">Ответ</h4>
<ul>
  <li><span style="font-weight: bold; color: #388E3C;">Статус 200</span>: Статистика успешно возвращена.
    <pre><code style="color: #FF9800;">{
  "original_url": "http://example.com",
  "created_at": "2025-04-03T12:00:00",
  "visit_count": 125,
  "last_access_at": "2025-04-03T13:00:00"
}</code></pre>
  </li>
  <li><span style="font-weight: bold; color: #F44336;">Статус 404</span>: Короткая ссылка не найдена.
    <pre><code style="color: #FF9800;">{
  "detail": "Short link not found"
}</code></pre>
  </li>
</ul>



<h3 style="color: #4CAF50;">GET /links/search</h3>

<h4 style="font-weight: bold; color: #2196F3;">Описание</h4>
<p>Этот эндпоинт позволяет искать короткую ссылку по её оригинальному URL. Сначала выполняется поиск в Redis, если ссылка не найдена — осуществляется поиск в базе данных. Результат кэшируется в Redis для последующих запросов.</p>

<ul>
  <li>Параметр <code>original_url</code> должен быть корректным URL-адресом, начинающимся с <code>http://</code> или <code>https://</code>.</li>
  <li>В случае нахождения ссылки в Redis, она будет возвращена напрямую.</li>
  <li>Если ссылка не найдена в Redis, выполняется поиск в базе данных, и результат кэшируется в Redis для ускорения будущих запросов.</li>
</ul>

<h4 style="font-weight: bold; color: #2196F3;">Запрос</h4>
<ul>
  <li><span style="font-weight: bold; color: #00796B;">Метод</span>: <span style="color: #009688;">GET</span></li>
  <li><span style="font-weight: bold; color: #00796B;">URL</span>: <code style="color: #009688;">/links/search</code></li>
  <li><span style="font-weight: bold; color: #00796B;">Параметры запроса</span>: 
    <ul>
      <li><span style="font-weight: bold; color: #00796B;">original_url</span>: <code style="color: #009688;">string</code>, обязательный параметр, URL для поиска короткой ссылки.</li>
    </ul>
  </li>
</ul>

<h4 style="font-weight: bold; color: #2196F3;">Ответ</h4>
<ul>
  <li><span style="font-weight: bold; color: #388E3C;">Статус 200</span>: Успешный запрос, короткая ссылка найдена и возвращена.
    <pre><code style="color: #FF9800;">{
  "short_code": "abc123",
  "original_url": "http://example.com"
}</code></pre>
  </li>
  <li><span style="font-weight: bold; color: #F44336;">Статус 400</span>: Ошибка валидации URL.
    <pre><code style="color: #FF9800;">{
  "detail": "Некорректный URL"
}</code></pre>
  </li>
  <li><span style="font-weight: bold; color: #F44336;">Статус 404</span>: Короткая ссылка не найдена для предоставленного URL.
    <pre><code style="color: #FF9800;">{
  "detail": "Short link not found for the provided URL"
}</code></pre>
  </li>
</ul>






<h3 style="color: #4CAF50;">GET /archive/stats</h3>

<h4 style="font-weight: bold; color: #2196F3;">Описание</h4>
<p>Этот эндпоинт позволяет авторизованному пользователю получить статистику по архивированным посещениям его коротких ссылок. Данные группируются по паре <code>short_code</code> – <code>original_url</code>.</p>

<ul>
  <li>Только авторизованный пользователь может просматривать статистику своих ссылок.</li>
  <li>Можно передать параметр <code>short_code</code> для фильтрации по конкретной короткой ссылке.</li>
</ul>

<h4 style="font-weight: bold; color: #2196F3;">Запрос</h4>
<ul>
  <li><span style="font-weight: bold; color: #00796B;">Метод</span>: <span style="color: #009688;">GET</span></li>
  <li><span style="font-weight: bold; color: #00796B;">URL</span>: <code style="color: #009688;">/archive/stats</code></li>
  <li><span style="font-weight: bold; color: #00796B;">Параметры запроса</span>: 
    <ul>
      <li><span style="font-weight: bold; color: #00796B;">short_code</span>: <code style="color: #009688;">string</code>, опциональный параметр, позволяет отфильтровать статистику по конкретной короткой ссылке.</li>
    </ul>
  </li>
</ul>

<h4 style="font-weight: bold; color: #2196F3;">Ответ</h4>
<ul>
  <li><span style="font-weight: bold; color: #388E3C;">Статус 200</span>: Успешный запрос, возвращает архивированную статистику.
    <pre><code style="color: #FF9800;">{
  "short_code_1": [
    {
      "original_url": "https://example.com",
      "timestamp": "2025-04-03T12:34:56",
      "domain_1st": "example.com",
      "domain_2nd": "sub.example.com",
      "ip_address": "192.168.1.1",
      "device_type": "mobile",
      "country": "US",
      "referer": "https://google.com",
      "archived_at": "2025-04-02T10:00:00",
      "archival_reason": "expired"
    }
  ],
  "short_code_2": [
    {
      "original_url": "https://another.com",
      "timestamp": "2025-04-01T15:20:30",
      "domain_1st": "another.com",
      "domain_2nd": null,
      "ip_address": "203.0.113.42",
      "device_type": "desktop",
      "country": "DE",
      "referer": "https://facebook.com",
      "archived_at": "2025-04-01T18:45:00",
      "archival_reason": "deleted by user"
    }
  ]
}</code></pre>
  </li>
  <li><span style="font-weight: bold; color: #F44336;">Статус 400</span>: Ошибка в параметрах запроса.
    <pre><code style="color: #FF9800;">{
  "detail": "Некорректные параметры запроса"
}</code></pre>
  </li>
  <li><span style="font-weight: bold; color: #F44336;">Статус 401</span>: Требуется авторизация.
    <pre><code style="color: #FF9800;">{
  "detail": "Неавторизованный доступ"
}</code></pre>
  </li>
</ul>



<h3 style="color: #4CAF50;">GET /active-links/stats</h3>

<h4 style="font-weight: bold; color: #2196F3;">Описание</h4>
<p>Этот эндпоинт позволяет получать статистику по активным визитам для авторизованного пользователя. Статистика группируется по паре "короткая ссылка - оригинальная ссылка". Можно фильтровать статистику по конкретной короткой ссылке, передав её в параметре запроса.</p>

<ul>
  <li>Параметр <code>short_code</code> является необязательным. Если передан, то будут возвращены статистические данные только для указанной короткой ссылки.</li>
  <li>Если не передан фильтр, будут возвращены данные для всех активных ссылок пользователя.</li>
  <li>Все данные по визитам включают информацию о времени визита, доменах, типах устройств, IP-адресах и других параметрах.</li>
</ul>

<h4 style="font-weight: bold; color: #2196F3;">Запрос</h4>
<ul>
  <li><span style="font-weight: bold; color: #00796B;">Метод</span>: <span style="color: #009688;">GET</span></li>
  <li><span style="font-weight: bold; color: #00796B;">URL</span>: <code style="color: #009688;">/active-links/stats</code></li>
  <li><span style="font-weight: bold; color: #00796B;">Параметры запроса</span>: 
    <ul>
      <li><span style="font-weight: bold; color: #00796B;">short_code</span>: <code style="color: #009688;">string</code> (необязательный параметр), короткая ссылка для фильтрации.</li>
    </ul>
  </li>
</ul>

<h4 style="font-weight: bold; color: #2196F3;">Ответ</h4>
<ul>
  <li><span style="font-weight: bold; color: #388E3C;">Статус 200</span>: Успешный запрос, статистика по активным визитам возвращена.
    <pre><code style="color: #FF9800;">{
  "abc123": [
    {
      "timestamp": "2025-04-01T10:00:00Z",
      "domain_1st": "example",
      "domain_2nd": "com",
      "ip_address": "192.168.1.1",
      "device_type": "mobile",
      "country": "RU",
      "referer": "http://referrer.com"
    }
  ]
}</code></pre>
  </li>
  <li><span style="font-weight: bold; color: #F44336;">Статус 400</span>: Ошибка, если короткая ссылка указана некорректно.
    <pre><code style="color: #FF9800;">{
  "detail": "Некорректный short_code"
}</code></pre>
  </li>
  <li><span style="font-weight: bold; color: #F44336;">Статус 404</span>: Если не найдены активные визиты для указанного пользователя.
    <pre><code style="color: #FF9800;">{
  "detail": "Не найдено активных визитов для данного пользователя"
}</code></pre>
  </li>
</ul>



<h3 style="color: #4CAF50;">Фоновая задача для архивации устаревших ссылок и визитов</h3>

<h4 style="font-weight: bold; color: #2196F3;">Описание</h4>
<p>Этот фоновый процесс выполняет архивацию устаревших коротких ссылок и их визитов, а также очищает связанные записи в Redis. Он запускается по расписанию (каждый час( по заданию раз в минуту, дабы удалить ссылку с точностью до минуты) или в зависимости от конфигурации) и выполняет следующие шаги:</p>

<ul>
  <li>Находит все короткие ссылки, срок действия которых истёк, включая автоматические истечения.</li>
  <li>Переносит устаревшие ссылки и их связанные визиты в архивные таблицы базы данных.</li>
  <li>Удаляет архивируемые ссылки и визиты из основных таблиц базы данных.</li>
  <li>Удаляет связанные данные из кэша Redis, если они там присутствуют.</li>
  <li>Использует транзакции для атомарности операций с базой данных, гарантируя, что все изменения будут либо полностью выполнены, либо отменены в случае ошибки.</li>
</ul>

<h4 style="font-weight: bold; color: #2196F3;">Запрос</h4>
<p>Данная функция является фоновым процессом, который не требует непосредственного запроса от пользователя. Он запускается автоматически через определённые промежутки времени, настроенные в коде.</p>

<h4 style="font-weight: bold; color: #2196F3;">Ответ</h4>
<ul>
  <li><span style="font-weight: bold; color: #388E3C;">Статус 200</span>: Успешно завершена операция архивации, все устаревшие ссылки и визиты были перемещены в архив.</li>
  <li><span style="font-weight: bold; color: #F44336;">Статус 500</span>: Ошибка при попытке архивации данных.
    <pre><code style="color: #FF9800;">{
  "detail": "Ошибка при переносе ссылок в архив"
}</code></pre>
  </li>
</ul>



<h3 style="color: #4CAF50;">Таблица User</h3>

<h4 style="font-weight: bold; color: #2196F3;">Описание</h4>
<p>Таблица <code>users</code> хранит информацию о пользователях, зарегистрированных в системе. Каждый пользователь может создавать и архивировать короткие ссылки, которые сохраняются в таблицах <code>short_links</code> и <code>short_links_archive</code>.</p>

<ul>
  <li><code>id</code>: Уникальный идентификатор пользователя (первичный ключ).</li>
  <li><code>username</code>: Имя пользователя, которое должно быть уникальным.</li>
  <li><code>email</code>: Адрес электронной почты пользователя, который также должен быть уникальным.</li>
  <li><code>password</code>: Хэш пароля пользователя.</li>
  <li><code>links</code>: Связь с таблицей <code>short_links</code>, где хранятся активные короткие ссылки пользователя.</li>
  <li><code>archived_links</code>: Связь с таблицей <code>short_links_archive</code>, где хранятся архивные ссылки пользователя.</li>
</ul>



<h3 style="color: #4CAF50;">Таблица ShortLink</h3>

<h4 style="font-weight: bold; color: #2196F3;">Описание</h4>
<p>Таблица <code>short_links</code> содержит активные короткие ссылки, созданные пользователями. Каждая запись включает в себя оригинальный URL, короткий код, время создания и срок действия ссылки. Также сохраняются данные о визитах по каждой ссылке.</p>

<ul>
  <li><code>id</code>: Уникальный идентификатор записи (первичный ключ).</li>
  <li><code>user_id</code>: Идентификатор пользователя, которому принадлежит короткая ссылка (внешний ключ на таблицу <code>users</code>).</li>
  <li><code>short_code</code>: Уникальный короткий код для ссылки.</li>
  <li><code>original_url</code>: Оригинальный URL, на который ведёт короткая ссылка.</li>
  <li><code>created_at</code>: Время создания короткой ссылки.</li>
  <li><code>expires_at</code>: Время истечения срока действия короткой ссылки (если задано).</li>
  <li><code>last_access_at</code>: Время последнего доступа к ссылке.</li>
  <li><code>auto_expires_at</code>: Автоматическое время истечения срока действия ссылки (если задано).</li>
  <li><code>visits</code>: Связь с таблицей <code>visits</code>, где хранятся данные о визитах по этой короткой ссылке.</li>
  <li><code>user</code>: Связь с таблицей <code>users</code>, чтобы определить владельца короткой ссылки.</li>
</ul>



<h3 style="color: #4CAF50;">Таблица ShortLinkArchive</h3>

<h4 style="font-weight: bold; color: #2196F3;">Описание</h4>
<p>Таблица <code>short_links_archive</code> содержит архивные записи коротких ссылок, которые были удалены или истекли. Эти записи сохраняются с информацией о причине архивации и времени архивации. Данные по визитам, связанным с этими ссылками, также переносятся в архив.</p>

<ul>
  <li><code>id</code>: Уникальный идентификатор записи (первичный ключ).</li>
  <li><code>user_id</code>: Идентификатор пользователя, которому принадлежала ссылка (внешний ключ на таблицу <code>users</code>).</li>
  <li><code>short_code</code>: Короткий код ссылки, которая была архивирована.</li>
  <li><code>original_url</code>: Оригинальный URL, на который вела короткая ссылка.</li>
  <li><code>created_at</code>: Время создания короткой ссылки.</li>
  <li><code>expires_at</code>: Время истечения срока действия короткой ссылки (если применимо).</li>
  <li><code>last_access_at</code>: Время последнего доступа к ссылке.</li>
  <li><code>auto_expires_at</code>: Автоматическое время истечения срока действия ссылки (если применимо).</li>
  <li><code>archived_at</code>: Время архивации ссылки.</li>
  <li><code>archival_reason</code>: Причина архивации (например, истёк срок действия, удалена пользователем и т.д.).</li>
  <li><code>visits_archive</code>: Связь с таблицей <code>visit_archives</code>, где хранятся архивные визиты по этой короткой ссылке.</li>
  <li><code>user</code>: Связь с таблицей <code>users</code>, чтобы определить владельца архивной короткой ссылки.</li>
</ul>




<h3 style="color: #4CAF50;">Таблица Visit</h3>

<h4 style="font-weight: bold; color: #2196F3;">Описание</h4>
<p>Таблица <code>visits</code> содержит информацию о каждом визите по активной короткой ссылке. Для каждого визита сохраняется время, IP-адрес пользователя, тип устройства, страна и другие параметры.</p>

<ul>
  <li><code>id</code>: Уникальный идентификатор визита (первичный ключ).</li>
  <li><code>owner</code>: Идентификатор пользователя, который совершил визит (внешний ключ на таблицу <code>users</code>).</li>
  <li><code>timestamp</code>: Время визита.</li>
  <li><code>short_code</code>: Короткий код ссылки, по которой был осуществлён визит.</li>
  <li><code>original_url</code>: Оригинальный URL, на который ведёт короткая ссылка.</li>
  <li><code>domain_1st</code>: Домен первого уровня в URL.</li>
  <li><code>domain_2nd</code>: Домен второго уровня в URL.</li>
  <li><code>ip_address</code>: IP-адрес пользователя, совершившего визит.</li>
  <li><code>device_type</code>: Тип устройства (например, mobile или desktop).</li>
  <li><code>country</code>: Страна, откуда был совершен визит.</li>
  <li><code>referer</code>: URL-адрес, с которого пришёл пользователь (реферер).</li>
  <li><code>short_link</code>: Связь с таблицей <code>short_links</code>, чтобы определить, к какой ссылке относится визит.</li>
</ul>



<h3 style="color: #4CAF50;">Таблица VisitArchive</h3>

<h4 style="font-weight: bold; color: #2196F3;">Описание</h4>
<p>Таблица <code>visit_archives</code> хранит архивные записи визитов, которые относятся к архивированным коротким ссылкам. Эти визиты сохраняются с информацией о времени архивации и причине архивации.</p>

<ul>
  <li><code>id</code>: Уникальный идентификатор записи (первичный ключ).</li>
  <li><code>owner</code>: Идентификатор пользователя, совершившего визит (внешний ключ на таблицу <code>users</code>).</li>
  <li><code>timestamp</code>: Время визита.</li>
  <li><code>short_code</code>: Короткий код ссылок, по которым были совершены визиты.</li>
  <li><code>original_url</code>: Оригинальный URL, на который вела короткая ссылка.</li>
  <li><code>domain_1st</code>: Домен первого уровня в URL.</li>
  <li><code>domain_2nd</code>: Домен второго уровня в URL.</li>
  <li><code>ip_address</code>: IP-адрес пользователя, совершившего визит.</li>
  <li><code>device_type</code>: Тип устройства, с которого был совершен визит.</li>
  <li><code>country</code>: Страна, откуда был совершен визит.</li>
  <li><code>referer</code>: Реферер визита.</li>
  <li><code>archived_at</code>: Время архивации визита.</li>
  <li><code>archival_reason</code>: Причина архивации визита.</li>
  <li><code>archived_link</code>: Связь с архивной короткой ссылкой в таблице <code>short_links_archive</code>.</li>
</ul>
