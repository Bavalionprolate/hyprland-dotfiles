import json
from pathlib import Path

CACHE_DIR = Path.home() / ".cache"
HIDDEN_APPS_FILE = CACHE_DIR / "hidden_apps.json"

hidden_apps = set()

def load_hidden_apps():
    global hidden_apps
    if HIDDEN_APPS_FILE.exists():
        with open(HIDDEN_APPS_FILE, "r") as file:
            hidden_apps = set(json.load(file))


def save_hidden_apps():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    with open(HIDDEN_APPS_FILE, "w") as file:
        json.dump(list(hidden_apps), file)

def hide_app(app_id):
    hidden_apps.add(app_id)
    save_hidden_apps()

def show_app(app_id):
    hidden_apps.discard(app_id)
    save_hidden_apps()

def is_hidden(app_id):
    return app_id in hidden_apps

load_hidden_apps()
