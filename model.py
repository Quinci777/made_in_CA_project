import concurrent.futures
import glob
from pathlib import Path
from openai import OpenAI

def call_gpt(prompt):
    response = OpenAI().chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# Чтение описания вакансии
job = Path("files/Job description.txt").read_text()
cv_files = glob.glob("files/candidates/*.txt")

# Определение запроса для оценки кандидатов
evaluation_prompt = """
Вы эксперт по подбору персонала.
Ниже приведено резюме кандидата на следующую вакансию: {job}.
Оцените кандидата. Напишите плюсы, минусы и ваши личные впечатления.

{cv}
"""

def evaluate_candidate(cv_file):
    cv = Path(cv_file).read_text()
    return call_gpt(evaluation_prompt.format(job=job, cv=cv))

# Оценка всех кандидатов 
with concurrent.futures.ThreadPoolExecutor() as executor:
    candidate_evaluations = list(executor.map(evaluate_candidate, cv_files))

# Определение запроса для финальной рекомендации
final_recommendation_prompt = """
Вы эксперт по подбору персонала.
Ниже приведены оценки нескольких кандидатов на следующую вакансию: {job}.

{candidate_evaluations}

На основе этой информации выберите наиболее подходящего кандидата.
Выберите одного кандидата и объясните свой выбор в нескольких предложениях.
"""

# Генерация финальной рекомендации
final_recommendation = call_gpt(final_recommendation_prompt.format(
    job=job,
    candidate_evaluations="\n\n".join(candidate_evaluations)
))

# Сохранение в файл
Path("files/Recommendation.txt").write_text(final_recommendation)

# Вывод финальной рекомендации
print(final_recommendation)
