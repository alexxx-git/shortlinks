import redis

# Подключение с паролем
r = redis.StrictRedis(host='localhost', port=6379, password='mypassword')

# Проверка подключения
print(r.ping())  # Ожидаем True
