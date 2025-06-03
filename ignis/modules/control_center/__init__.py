from ignis.widgets import Widget
from ignis.app import IgnisApp
from .volume import volume_control
from .quick_settings import quick_settings
from .user import user
from .notification_center import notification_center
from .media import media
from datetime import datetime

app = IgnisApp.get_default()

def control_center_widget() -> Widget.Box:
    current_date = datetime.now()
    calendar = Widget.Calendar(
        day=current_date.day,
        month=current_date.month - 1,
        year=current_date.year,
        show_day_names=True,
        show_heading=True,
        css_classes=["calendar-widget"]
    )

    return Widget.Box(
        vertical=True,
        css_classes=["control-center"],
        child=[
            Widget.Scroll(
                vexpand=True,
                child=Widget.Box(
                    vertical=True,
                    css_classes=["control-center-content"],
                    spacing = 15,
                    child=[
                        Widget.Box(
                            vertical=True,
                            css_classes=["control-center-widget"],
                            child=[user(), quick_settings(), volume_control(), media()],
                        ),
                        notification_center(),
                        calendar,
                    ],
                ),
            ),
        ],
    )

def control_center(monitor_id: int = 0) -> Widget.RevealerWindow:
    revealer = Widget.Revealer(
        child=control_center_widget(),
        transition_duration=300,
        transition_type="slide_left",
        reveal_child=True
    )
    box = Widget.Box(
        child=[
            revealer,
        ],
    )

    return Widget.RevealerWindow(
        visible=False,
        popup=False,
        kb_mode="on_demand",
        layer="top",
        anchor=["top", "right", "bottom"],
        namespace=f"ignis_CONTROL_CENTER_{monitor_id}",
        monitor=monitor_id,
        child=box,
        revealer=revealer,
    )
