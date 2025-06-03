from .qs_button import QSButton
from options import settings

def dnd_button() -> QSButton:
    return QSButton(
        label=settings.notifications.bind("dnd", lambda value: "Выкл." if value else "Вкл."),
        icon_name=settings.notifications.bind(
            "dnd",
            transform=lambda value: "user-busy"
            if value
            else "user-available",
        ),
        on_activate=lambda x: setattr(settings.notifications, "dnd", not settings.notifications.dnd),
        on_deactivate=lambda x: setattr(settings.notifications, "dnd", not settings.notifications.dnd),
        active=settings.notifications.bind("dnd"),
    )
