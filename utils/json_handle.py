import json


def load_json(fp):
    with open(fp, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def save_json(fp, data):
    with open(fp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
