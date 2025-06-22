from __future__ import annotations
import os
import re
import google.generativeai as genai

# Инициализация Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

# Функция для очистки markdown-разметки
def clean_markdown(text):
    """Удаляет markdown-разметку из текста"""
    # Удаляем ** для жирного текста
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    # Удаляем * для курсива
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    # Удаляем ` для кода
    text = re.sub(r'`(.*?)`', r'\1', text)
    # Удаляем # для заголовков
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
    # Удаляем лишние пробелы
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text.strip()

# Шаблоны
evaluation_prompt = """
Вы эксперт по подбору персонала.
Ниже приведено резюме кандидата на следующую вакансию: {job}.
Оцените кандидата. Напишите плюсы, минусы и ваши личные впечатления.

ВАЖНО: Не используйте markdown-разметку (**, *, `, #). Пишите обычный текст.

{cv}
"""

final_recommendation_prompt = """
Вы эксперт по подбору персонала.
На основе следующей оценки кандидата на вакансию:

{evaluation}

Скажите, рекомендуете ли вы нанять этого кандидата. Обоснуйте решение в 2-3 предложениях.

ВАЖНО: Не используйте markdown-разметку (**, *, `, #). Пишите обычный текст.
"""

questions_for_HR_prompt = '''
Вы эксперт по подбору персонала.
На основе следующей рекомендации кандидата на вакансию:

{recommendation}

Если кандидат рекомендован на вакансию, составьте 5 вопросов кандидату, которые можно было бы задать на собеседовании.
Если же кандидат не рекомендован, то напиши: Нет вопросов

ВАЖНО: Не используйте markdown-разметку (**, *, `, #). Пишите обычный текст.
'''

# Вызов модели Gemini
def call_gemini(prompt):
    response = model.generate_content(prompt)
    # Очищаем markdown-разметку из ответа
    return clean_markdown(response.text)
