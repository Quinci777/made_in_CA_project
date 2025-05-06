from models import UserInDB

# Имитация базы данных пользователей
fake_users_db = {}

# Функция для получения пользователя из базы данных
def get_user_from_db(username: str) -> Optional[UserInDB]:
    if username in fake_users_db:
        return fake_users_db[username]
    return None

# Функция для создания пользователя
def create_user_in_db(user: UserInDB):
    fake_users_db[user.username] = user
