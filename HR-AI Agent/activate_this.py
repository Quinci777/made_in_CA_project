from __future__ import annotations
import os
import site
import sys
import glob
import time
from pathlib import Path
import concurrent.futures
import google.generativeai as genai

# Инициализация Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

# Шаблоны
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

Если кандидат рекомендован на вакансию, составьте 5 вопросов кандидату, которые можно было бы задать на собеседовании.
Если же кандидат не рекомендован, то напиши: Нет вопросов
'''

# Вызов модели Gemini
def call_gemini(prompt):
    response = model.generate_content(prompt)
    return response.text.strip()
