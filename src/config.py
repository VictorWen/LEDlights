import os
import json

CONFIG = {}
if os.path.exists("config.json"):
    with open("config.json", 'r') as file:
        CONFIG = json.load(file)


def config(path, default=None):
    tokens = path.split('.')
    obj = CONFIG
    for token in tokens:
        if token in obj:
            obj = obj[token]
        else:
            return default
    if obj is None:
        return default
    else:
        return obj