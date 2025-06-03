from options import settings

def hide_app(app_id: str) -> bool:
    return settings.apps.hide_app(app_id)

def show_app(app_id: str) -> bool:
    return settings.apps.show_app(app_id)

def is_hidden(app_id: str) -> bool:
    return settings.apps.is_hidden(app_id)