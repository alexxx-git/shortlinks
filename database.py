import asyncpg
import asyncio
from typing import List


async def connect_to_db():
    # Указываем параметры подключения
    conn = await asyncpg.connect(user='postgres', password='mypassword', database='mydb', host='127.0.0.1', port=5432)
    return conn


async def create_table(conn):
    # Пример создания таблицы
    await conn.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        name TEXT,
        age INT
    )
    ''')
    print("Table 'users' created.")


async def insert_user(conn, name: str, age: int):
    # Пример вставки данных
    await conn.execute('''
    INSERT INTO users(name, age) VALUES($1, $2)
    ''', name, age)
    print(f"Inserted user {name}, {age}.")


async def fetch_users(conn) -> List[dict]:
    # Пример выборки данных
    rows = await conn.fetch('SELECT * FROM users')
    return rows


async def main():
    # Подключаемся к базе данных
    conn = await connect_to_db()

    try:
        # Создаем таблицу
        await create_table(conn)

        # Вставляем пользователей
        await insert_user(conn, 'Alice', 30)
        await insert_user(conn, 'Bob', 25)

        # Получаем всех пользователей
        users = await fetch_users(conn)
        for user in users:
            print(f"User {user['id']}: {user['name']}, {user['age']}")

    finally:
        # Закрываем соединение
        await conn.close()


# Запускаем асинхронную функцию
if __name__ == "__main__":
    asyncio.run(main())
