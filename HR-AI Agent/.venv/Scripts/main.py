from fastapi import FastAPI, UploadFile, File, Request, Depends, HTTPException, status, BackgroundTasks, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import google.generativeai as genai
import time
from typing import List
import os

from fastapi import Form

from docx import Document
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

pdfmetrics.registerFont(TTFont("DejaVuSans", "DejaVuSans.ttf"))

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

@app.get("/download_questions/")
async def download_questions(
    request: Request,
    background_tasks: BackgroundTasks,
    format: str = Query("txt", enum=["txt", "docx", "pdf"])
):
    questions_text = "\n".join(temp_questions)

    if format == "txt":
        file_path = "questions.txt"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(questions_text)
        media_type = "text/plain"
        filename = "HR_questions.txt"

    elif format == "docx":
        file_path = "questions.docx"
        doc = Document()
        for line in questions_text.split("\n"):
            doc.add_paragraph(line)
        doc.save(file_path)
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        filename = "HR_questions.docx"

    elif format == "pdf":
        file_path = "questions.pdf"
        c = canvas.Canvas(file_path, pagesize=A4)
        c.setFont("DejaVuSans", 12)  # Шрифт уже зарегистрирован
        width, height = A4
        y = height - 50
        text_obj = c.beginText(50, y)
        text_obj.setFont("DejaVuSans", 12)
        for line in questions_text.split("\n"):
            text_obj.textLine(line)
            y -= 20
            if y < 50:
                c.drawText(text_obj)
                c.showPage()
                text_obj = c.beginText(50, height - 50)
                text_obj.setFont("DejaVuSans", 12)
        c.drawText(text_obj)
        c.save()
        media_type = "application/pdf"
        filename = "HR_questions.pdf"