import concurrent.futures
import glob
from pathlib import Path
from openai import OpenAI
import time

client = OpenAI(api_key="ваш api с https://platform.openai.com/assistants/asst_S8W94anMLpfILBeAkCMmtfpJ")

def call_gpt(prompt):
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # Используйте gpt-3.5-turbo, если gpt-4o-mini недоступен
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# Проверка и чтение описания вакансии
job_path = Path("files/Job description.txt")
if not job_path.exists():
    raise FileNotFoundError(f"Файл {job_path} не найден.")
job = job_path.read_text(encoding="utf-8")

# Поиск файлов с резюме кандидатов
cv_files = glob.glob("files/candidates/*.txt")

# Определение запроса для оценки кандидатов
evaluation_prompt = """
Вы эксперт по подбору персонала.
Ниже приведено резюме кандидата на следующую вакансию: {job}.
Оцените кандидата. Напишите плюсы, минусы и ваши личные впечатления.

{cv}
"""

def evaluate_candidate(cv_file):
    cv = Path(cv_file).read_text(encoding="utf-8")
    time.sleep(1)  # Задержка в 1 секунду между запросами
    return call_gpt(evaluation_prompt.format(job=job, cv=cv))

# Оценка всех кандидатов
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:  # Ограничьте количество потоков
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
Path("files/Recommendation.txt").write_text(final_recommendation, encoding="utf-8")

# Вывод финальной рекомендации
print(final_recommendation)
