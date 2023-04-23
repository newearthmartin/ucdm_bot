import json

data = None

DB_FILE = 'db.json'


def write_data():
    with open(DB_FILE, 'w') as f:
        f.write(json.dumps(data, indent=2))


def get_data():
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
