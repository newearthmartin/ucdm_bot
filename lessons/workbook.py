import os
import json
from datetime import date
from django.conf import settings

workbook_structure = None
workbook_cache = {}
WORKBOOK_PATH = os.path.join(settings.BASE_DIR, 'acim_workbook')


def get_day_texts(day: int) -> list[str]:
    """
    :param day: 0-based lesson day
    """
    if day in workbook_cache:
        return workbook_cache[day]

    global workbook_structure
    if not workbook_structure:
        with open(f'{WORKBOOK_PATH}/workbook_structure.json') as f:
            workbook_structure = json.loads(f.read())

    rv = []
    for file in workbook_structure[day]:
        with open(f'{WORKBOOK_PATH}/{settings.WORKBOOK_LANGUAGE}/{file}') as f:
            text = f.read()
            rv.append(text)
    workbook_cache[day] = rv
    return rv


def get_day_lesson_number(today: date) -> int:
    jan1 = date(today.year, 1, 1)
    lesson_number = (today - jan1).days
    if lesson_number >= 365:  # for years with 366 days
        return None
    return lesson_number
