from .qs_button import QSButton
from ignis.services.notifications import NotificationService

notifications = NotificationService.get_default()


def dnd_button() -> QSButton:
    return QSButton(
        label=notifications.bind("dnd", lambda value: "Выкл." if value else "Вкл."),
        icon_name=notifications.bind(
            "dnd",
            transform=lambda value: "user-busy"
            if value
            else "user-available",
        ),
        on_activate=lambda x: notifications.set_dnd(not notifications.dnd),
        on_deactivate=lambda x: notifications.set_dnd(not notifications.dnd),
        active=notifications.bind("dnd"),
    )
