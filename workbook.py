import json

workbook_structure = None
workbook_cache = {}
WORKBOOK_PATH = 'acim_workbook/es'


def get_day_texts(day: int) -> list[str]:
    """
    @param day: zero based lesson number
    """
    if day in workbook_cache:
        return workbook_cache[day]

    global workbook_structure
    if not workbook_structure:
        with open(f'{WORKBOOK_PATH}/estructura.json') as f:
            workbook_structure = json.loads(f.read())

    rv = []
    for file in workbook_structure[day]:
        with open(f'{WORKBOOK_PATH}/{file}') as f:
            text = f.read()
            rv.append(text)
    workbook_cache[day] = rv
    return rv

