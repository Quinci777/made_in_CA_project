from __future__ import annotations
import os
import site
import sys
import glob
import time
from pathlib import Path
import concurrent.futures
import google.generativeai as genai

# Инициализация клиента Gemini
genai.configure(api_key="your_api_key")
model = genai.GenerativeModel("gemini-1.5-flash")

# Чтение описания вакансии
job_path = Path("files/Job description.txt")
if not job_path.exists():
    raise FileNotFoundError(f"Файл {job_path} не найден.")
job = job_path.read_text(encoding="utf-8")

# Поиск резюме кандидатов
cv_files = glob.glob("files/candidates/*.txt")

# Шаблон запроса для оценки кандидатов
evaluation_prompt = """
Вы эксперт по подбору персонала.
Ниже приведено резюме кандидата на следующую вакансию: {job}.
Оцените кандидата. Напишите плюсы, минусы и ваши личные впечатления.

{cv}
"""

# Функция отправки запроса к Gemini
def call_gemini(prompt):
    response = model.generate_content(prompt)
    return response.text.strip()

# Оценка каждого кандидата
def evaluate_candidate(cv_file):
    cv = Path(cv_file).read_text(encoding="utf-8")
    time.sleep(1)  # Небольшая задержка между запросами
    return call_gemini(evaluation_prompt.format(job=job, cv=cv))

# Оценка всех резюме параллельно
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    candidate_evaluations = list(executor.map(evaluate_candidate, cv_files))

# Формирование финального запроса
final_recommendation_prompt = """
Вы эксперт по подбору персонала.
Ниже приведены оценки нескольких кандидатов на следующую вакансию: {job}.

{candidate_evaluations}

На основе этой информации выберите наиболее подходящего кандидата.
Выберите одного кандидата и объясните свой выбор в нескольких предложениях.
"""

# Получение финальной рекомендации
final_recommendation = call_gemini(final_recommendation_prompt.format(
    job=job,
    candidate_evaluations="\n\n".join(candidate_evaluations)
))

# Сохранение результата
Path("files/Recommendation.txt").write_text(final_recommendation, encoding="utf-8")

# Печать финальной рекомендации
print(final_recommendation)

# Шаблон вопроса для получения списка вопросов о рекомендованном кандидате
questions_for_HR_prompt = '''
Вы эксперт по подбору персонала.
На основе следующей рекомендации кандидата на вакансию:

{recommendation}

Если кандидат рекомендован на вакансию, составте 5 вопросов кандидату, которые можно было бы задать на собеседовании.
Если же кандидат не рекомендован, то выведи пустую строку
'''

questions_for_HR = call_gemini(questions_for_HR_prompt.format(final_recommendation))

Path("files/Question.txt").write_text(questions_for_HR, encoding="utf-8")

print(questions_for_HR)


try:
    abs_file = os.path.abspath(__file__)
except NameError as exc:
    msg = "You must use exec(open(this_file).read(), {'__file__': this_file}))"
    raise AssertionError(msg) from exc

bin_dir = os.path.dirname(abs_file)
base = bin_dir[: -len("Scripts") - 1]  # strip away the bin part from the __file__, plus the path separator

# prepend bin to PATH (this file is inside the bin directory)
os.environ["PATH"] = os.pathsep.join([bin_dir, *os.environ.get("PATH", "").split(os.pathsep)])
os.environ["VIRTUAL_ENV"] = base  # virtual env is right above bin directory
os.environ["VIRTUAL_ENV_PROMPT"] = "" or os.path.basename(base)  # noqa: SIM222

# add the virtual environments libraries to the host python import mechanism
prev_length = len(sys.path)
for lib in "..\\Lib\\site-packages".split(os.pathsep):
    path = os.path.realpath(os.path.join(bin_dir, lib))
    site.addsitedir(path.decode("utf-8") if "" else path)
sys.path[:] = sys.path[prev_length:] + sys.path[0:prev_length]

sys.real_prefix = sys.prefix
sys.prefix = base
