from ignis.widgets import Widget
from ignis.app import IgnisApp
from ignis.utils import Utils
from ignis.services.notifications import Notification, NotificationService
from ..control_center.notification_center import NotificationWidget
from options import settings

app = IgnisApp.get_default()
notifications = NotificationService.get_default()

class Popup(Widget.Box):
    def __init__(self, notification: Notification):
        widget = NotificationWidget(notification)
        widget.css_classes = ["notification-popup"]
        self._inner = Widget.Revealer(transition_type="slide_left", child=widget)
        self._outer = Widget.Revealer(transition_type="slide_down", child=self._inner)
        super().__init__(child=[self._outer], halign="end")

        notification.connect("dismissed", lambda x: self.destroy())

    def destroy(self):
        def box_destroy():
            box: Widget.Box = self.get_parent()
            if not box:
                return

            self.unparent()
            if len(notifications.popups) == 0:
                window: Widget.Window = box.get_parent()
                if not window:
                    return
                window.visible = False
            else:
                change_window_input_region(box)

        def outer_close():
            self._outer.reveal_child = False
            Utils.Timeout(self._outer.transition_duration, box_destroy)

        Utils.Timeout(self._outer.transition_duration, outer_close)


def on_notified(box: Widget.Box, notification: Notification, monitor: int) -> None:
    window: Widget.Window = app.get_window(f"ignis_CONTROL_CENTER_{monitor}")
    if window.visible and window.monitor == monitor:
        return

    app.open_window(f"ignis_NOTIFICATION_POPUP_{monitor}")
    popup = Popup(notification)
    box.prepend(popup)
    popup._outer.reveal_child = True
    Utils.Timeout(popup._outer.transition_duration, reveal_popup, box, popup)

def reveal_popup(box: Widget.Box, popup: Popup) -> None:
    popup._inner.set_reveal_child(True)
    change_window_input_region(box)


def change_window_input_region(box: Widget.Box) -> None:
    def callback() -> None:
        width = box.get_width()
        height = box.get_height()
        window: Widget.Window = box.get_parent()

        window.input_width = width
        window.input_height = height

    Utils.Timeout(ms=50, target=callback)

def notification_popup(monitor: int) -> Widget.Window:
    def handle_notification_or_dnd(self, notification=None) -> None:
        # Close popup window if DND is enabled
        if settings.notifications.dnd:
            window = app.get_window(f"ignis_NOTIFICATION_POPUP_{monitor}")
            if window:
                window.visible = False
            return

        # Show notification if one was provided
        if notification:
            on_notified(self, notification, monitor)

    notifications_box = Widget.Box(
        vertical=True,
        valign="start",
        setup=lambda self: [
            notifications.connect(
                "new_popup",
                lambda x, notification: handle_notification_or_dnd(self, notification),
            ),
            settings.notifications.connect_option(
                "dnd",
                lambda: handle_notification_or_dnd(self),
            ),
        ],
    )

    return Widget.Window(
        anchor=["right", "top", "bottom"],
        monitor=monitor,
        namespace=f"ignis_NOTIFICATION_POPUP_{monitor}",
        layer="top",
        child=notifications_box,
        visible=False,
        css_classes=["rec-unset"],
        style="min-width: 29rem;",
    )
