from __future__ import annotations
import os
import google.generativeai as genai
from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import current_user
from activate_this import call_gemini, evaluation_prompt, final_recommendation_prompt, questions_for_HR_prompt

# Flask Blueprint для основного функционала
main_bp = Blueprint('main', __name__)

# Главная страница
@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.form'))
    return redirect(url_for('auth.login'))

# Страница формы и обработка данных
@main_bp.route('/form', methods=['GET', 'POST'])
def form():
    if request.method == 'GET':
        return render_template('form.html')

    job_description_file = request.files.get('job_description_file')
    resume_files = request.files.getlist('files')

    if not job_description_file or not resume_files:
        return render_template('form.html', error='Пожалуйста, загрузите все файлы')

    job_description = job_description_file.read().decode('utf-8')
    evaluations, recommendations, questions = [], [], []

    for file in resume_files:
        cv_content = file.read().decode('utf-8')

        evaluation = call_gemini(evaluation_prompt.format(job=job_description, cv=cv_content))
        evaluations.append(evaluation)

        recommendation = call_gemini(final_recommendation_prompt.format(evaluation=evaluation))
        recommendations.append(recommendation)

        question = call_gemini(questions_for_HR_prompt.format(recommendation=recommendation))
        if 'Нет вопросов' not in question:
            questions.append(question)

    return render_template('form.html', evaluations=evaluations,
                           recommendations=recommendations, questions=questions)