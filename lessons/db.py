import os
import json
from pathlib import Path
from django.conf import settings

BASE_DIR = Path(__file__).parent.parent.absolute()
print(BASE_DIR, settings.BASE_DIR)
DB_FILE = os.path.join(BASE_DIR, 'db.json')
data = None


def db_set(key, val):
    data = __get_data()
    if val is None:
        if key in data: del data[key]
    else:
        data[key] = val
    __write_data()


def db_get(key, default_value=None):
    global data
    data = __get_data()
    if key in data:
        return data[key]
    if default_value is not None:
        data[key] = default_value
        return data[key]
    return None


def __write_data():
    with open(DB_FILE, 'w') as f:
        f.write(json.dumps(data, indent=2))


def __get_data():
    global data
    if data is None:
        try:
            with open(DB_FILE) as f:
                data = json.loads(f.read())
        except FileNotFoundError:
            data = {}
        except json.decoder.JSONDecodeError:
            print('JSON decode error - resetting db')
            data = {}
    return data
