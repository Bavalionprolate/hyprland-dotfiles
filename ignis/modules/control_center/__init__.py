from ignis.widgets import Widget
from ignis.app import IgnisApp
from .volume import volume_control
from .quick_settings import quick_settings
from .user import user
from .notification_center import notification_center
from .media import media 

app = IgnisApp.get_default()


def control_center_widget() -> Widget.Box:
    return Widget.Box(
        vertical=True,
        css_classes=["control-center"],
        child=[
            Widget.Box(
                vertical=True,
                css_classes=["control-center-widget"],
                child=[quick_settings(), volume_control(), media(), user()],
            ),
            notification_center(),
        ],
    )

def control_center() -> Widget.RevealerWindow:
    revealer = Widget.Revealer(
        child=control_center_widget(),
        transition_duration=100,
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
        anchor=["top", "right"],
        namespace="ignis_CONTROL_CENTER",
        child=box,
        revealer=revealer,
    )
