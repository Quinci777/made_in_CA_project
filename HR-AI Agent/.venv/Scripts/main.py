from fastapi import FastAPI, UploadFile, File, Request, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import google.generativeai as genai
import time
from typing import List
import os



app = FastAPI()


# Подключение папки со static-файлами
app.mount("/static", StaticFiles(directory="static"), name="static")

# Папка с HTML-шаблонами
templates = Jinja2Templates(directory="templates")

# Настроим OAuth2 для авторизации
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# функция для удаления временных файлов
def delete_file_after_use(file_path: str):
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        print(f"Error deleting file: {e}")


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
genai.configure(api_key="AIzaSyDhsoesbWHSJktDB55zPX6Fq8X6thxphfk")
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

questions_for_HR_prompt = '''
Вы эксперт по подбору персонала.
На основе следующей рекомендации кандидата на вакансию:

{recommendation}

Если кандидат рекомендован на вакансию, составте 5 вопросов кандидату, которые можно было бы задать на собеседовании.
Если же кандидат не рекомендован, то напиши: Нет вопросов
'''


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
    questions = []

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

        # Генерация вопросов для рекомендованого кандидата
        question_prompt = questions_for_HR_prompt.format(recommendation=recommendation)
        question = call_gemini(question_prompt)
        if 'Нет вопросов' not in question:
            questions.append(question)



    # глобальная переменная для хранения вопросов    
    global temp_questions
    temp_questions = questions

    return templates.TemplateResponse("form.html", {
        "request": request,
        "evaluations": evaluations,
        "recommendations": recommendations,
        "questions": questions
    })

@app.get("/download_questions/", response_class=HTMLResponse)
async def download_questions(request: Request, background_tasks: BackgroundTasks):
    #создаем временной файл для вопросов
    questions_text = "\n".join(temp_questions)
    temp_file_path = "questions.txt"
    with open(temp_file_path, "w", encoding="utf-8") as f:
        f.write(questions_text)

    # удаляем временной файл
    background_tasks.add_task(delete_file_after_use, temp_file_path)

    return FileResponse(
        temp_file_path,
        media_type="text/plain",
        filename="HR_questions.txt"
    )


