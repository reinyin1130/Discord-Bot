import os
import json

from config.default_json import user_data, shop_items, tarot_cards

FILES = {
    "user_data.json": user_data,
    "shop_items.json": shop_items,
    "tarot_cards.json": tarot_cards,
}


def init_json():
    for f in FILES:
        if not os.path.exists(f):
            with open(f, "w") as file:
                json.dump(FILES[f], file)
