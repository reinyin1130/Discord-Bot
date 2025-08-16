import os
import json

from config.default_json import user_data, shop_items, tarot_cards


def init_json():
    FILES = {
        "user_data.json": user_data,
        "shop_items.json": shop_items,
        "tarot_cards.json": tarot_cards,
    }

    for f in FILES:
        if not os.path.exists(f):
            with open(f, "w") as file:
                json.dump(FILES[f], file)


def load_json(fp):
    with open(fp, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def save_json(fp, data):
    with open(fp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
