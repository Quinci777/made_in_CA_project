from __future__ import annotations
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import current_user
from ai_model import call_gemini, evaluation_prompt, final_recommendation_prompt, questions_for_HR_prompt
import os
import re

main_bp = Blueprint('main', __name__)

# Фильтр для очистки markdown-разметки в шаблонах
@main_bp.app_template_filter('clean_markdown')
def clean_markdown_filter(text):
    """Удаляет markdown-разметку из текста для отображения в шаблоне"""
    if not text:
        return text
    # Удаляем ** для жирного текста
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    # Удаляем * для курсива
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    # Удаляем ` для кода
    text = re.sub(r'`(.*?)`', r'\1', text)
    # Удаляем # для заголовков
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
    return text.strip()

# Разрешенные расширения файлов
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx'}

def allowed_file(filename):
    """Проверяет, что расширение файла разрешено"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.form'))
    return redirect(url_for('auth.login'))

@main_bp.route('/form', methods=['GET', 'POST'])
def form():
    if request.method == 'GET':
        return render_template('form.html')

    job_description_file = request.files.get('job_description_file')
    resume_files = request.files.getlist('files')

    # Проверка загружены ли файлы
    if not job_description_file or not resume_files:
        flash('Пожалуйста, загрузите все файлы', 'error')
        return redirect(url_for('main.form'))

    # Проверка расширения файла с описанием вакансии
    if not allowed_file(job_description_file.filename):
        flash('Описание вакансии: разрешены только файлы .docx, .pdf, .txt', 'error')
        return redirect(url_for('main.form'))

    # Проверка расширений файлов резюме
    for file in resume_files:
        if not allowed_file(file.filename):
            flash(f'Резюме {file.filename}: разрешены только файлы .docx, .pdf, .txt', 'error')
            return redirect(url_for('main.form'))

    job_description = ""
    try:
        job_description = job_description_file.read().decode('utf-8')
    except UnicodeDecodeError:
        # Для PDF и DOCX может потребоваться специальная обработка
        flash('Ошибка чтения файла описания вакансии. Убедитесь, что файл в правильном формате.', 'error')
        return redirect(url_for('main.form'))

    evaluations, recommendations, questions = [], [], []

    for file in resume_files:
        try:
            cv_content = file.read().decode('utf-8')
        except UnicodeDecodeError:
            flash(f'Ошибка чтения файла {file.filename}. Убедитесь, что файл в правильном формате.', 'error')
            continue

        evaluation = call_gemini(evaluation_prompt.format(job=job_description, cv=cv_content))
        evaluations.append(evaluation)

        recommendation = call_gemini(final_recommendation_prompt.format(evaluation=evaluation))
        recommendations.append(recommendation)

        question = call_gemini(questions_for_HR_prompt.format(recommendation=recommendation))
        if 'Нет вопросов' not in question:
            questions.append(question)

    return render_template('form.html', evaluations=evaluations,
                         recommendations=recommendations, questions=questions)