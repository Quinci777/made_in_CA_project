from fastapi import FastAPI, UploadFile, File, Request, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import google.generativeai as genai
import time
from typing import List



app = FastAPI()


# Подключение папки со static-файлами
app.mount("/static", StaticFiles(directory="static"), name="static")

# Папка с HTML-шаблонами
templates = Jinja2Templates(directory="templates")

# Настроим OAuth2 для авторизации
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user_from_db(form_data.username)
    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Создание токена
    access_token = create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/profile", response_class=HTMLResponse)
async def profile(request: Request, token: str = Depends(oauth2_scheme)):
    # Проверка валидности токена
    user = get_user_from_token(token)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    return templates.TemplateResponse("profile.html", {"request": request, "user": user})



# Инициализация Gemini
genai.configure(api_key="AIzaSyA5oDiJCP5mMM8bZyU_5VKM5GtWvEVw_3s")
model = genai.GenerativeModel("gemini-1.5-flash")

evaluation_prompt = """
Вы эксперт по подбору персонала.
Ниже приведено резюме кандидата на следующую вакансию: {job}.
Оцените кандидата. Напишите плюсы, минусы и ваши личные впечатления.

{cv}
"""


final_recommendation_prompt = """
Вы эксперт по подбору персонала.
На основе следующей оценки кандидата на вакансию:

{evaluation}

Скажите, рекомендуете ли вы нанять этого кандидата. Обоснуйте решение в 2-3 предложениях.
"""


def call_gemini(prompt):
    response = model.generate_content(prompt)
    return response.text.strip()


@app.get("/", response_class=HTMLResponse)
async def form(request: Request):
    return templates.TemplateResponse("form.html", {"request": request})


@app.post("/evaluate/", response_class=HTMLResponse)
async def evaluate_candidates(request: Request, job_description_file: UploadFile = File(...),
                              files: List[UploadFile] = File(...)):
    # Чтение содержимого файла описания вакансии
    job_description = (await job_description_file.read()).decode("utf-8")

    evaluations = []
    recommendations = []

    # Обрабатываем каждый файл с резюме
    for file in files:
        cv_content = (await file.read()).decode("utf-8")
        prompt = evaluation_prompt.format(job=job_description, cv=cv_content)
        time.sleep(1)
        evaluation = call_gemini(prompt)
        evaluations.append(evaluation)

        # Генерация финальной рекомендации
        recommendation_prompt = final_recommendation_prompt.format(evaluation=evaluation)
        recommendation = call_gemini(recommendation_prompt)
        recommendations.append(recommendation)

    return templates.TemplateResponse("form.html", {
        "request": request,
        "evaluations": evaluations,
        "recommendations": recommendations
    })

