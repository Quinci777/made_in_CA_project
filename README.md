# HR-AI Agent


## О проекте
HR-AI Agent — это веб-приложение на FastAPI, которое помогает оценивать резюме кандидатов с помощью искусственного интеллекта Gemini (Google Generative AI).


## Функционал
- Загрузка вакансии и резюме через веб-интерфейс.
- Автоматическая оценка каждого кандидата (плюсы, минусы и впечатления).
- Генерация финальной рекомендации (стоит ли нанимать кандидата и почему).
- Авторизация пользователей через JWT (OAuth2).
- HTML-интерфейс с шаблонами Jinja2.
- Обработка нескольких резюме с помощью многопоточности.


## Как быстро развернуть приложение у себя на ПК с использованием Git и PyCharm

#### 0. Склонируйте репозиторий

```bash
git clone https://github.com/Quinci777/made_in_CA_project.git
```

#### 1. Создание виртуального окружения

Перейдите в папку проекта:

```bash
cd *место хранения проекта*\made_in_CA_project\HR-AI Agent
```

Создайте виртуальное окружение:

```bash
python -m venv .venv
```

Активируйте окружение:

```bash
..venv\Scripts\activate
```

#### 2. Установка зависимостей

После активации среды установите библиотеки:

```bash
pip install -r requirements.txt
```

#### 3. Настройка переменных окружения

Создайте файл .env в папке проекта \made_in_CA_project\HR-AI Agent\ и вставьте в него следующее содержимое:

```dotenv
SECRET_KEY=<ваш_случайный_ключ>
DATABASE_URL=sqlite:///users.db
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=<example@mail.com>
MAIL_PASSWORD=<ключ доступа к почте>
MAIL_DEFAULT_SENDER=denis.filatov200055@gmail.com
BASE_URL=http://127.0.0.1:5000
GEMINI_API_KEY=<ваш API_KEY>
PORT=8080
HOST=0.0.0.0
DEBUG_MODE=True
```

##### Как получить необходимые значения:

SECRET_KEY — впишите случайные символы, а лучше сгенерируйте с помощью Python:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

GEMINI_API_KEY — получите по адресу: https://makersuite.google.com/app

⚠️ Если DEBUG_MODE=True, вы можете не настраивать почту для подтверждения регистрации в .env, при этом автоматически создастся аккаунт:
```bash
Email: admin@debug.com
Пароль: admin
```
#### 4. Запуск приложения

Запустите проект через IDE или выполните в командной строке:

```bash
python run.py
```

Приложение откроется по адресу:

```
http://127.0.0.1:8080/
```

Если включен DEBUG_MODE=True, при первом запуске автоматически будет создан пользователь admin@debug.com с паролем admin.

