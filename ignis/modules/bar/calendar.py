import datetime
import math
from ignis.widgets import Widget
from ignis.utils import Utils
from ignis.app import IgnisApp

app = IgnisApp.get_default()

class Calendar(Widget.Box):
    def __init__(self, date=None):
        self.date = date or datetime.datetime.now()
        self.today = datetime.datetime.now().date()
        self.selected_date = self.date.date()

        self.header = self._create_header()
        self.days_grid = self._create_days_grid()

        super().__init__(
            vertical=True,
            css_classes=["calendar-widget"],
            child=[
                self.header,
                Widget.Box(
                    homogeneous=True,
                    css_classes=["calendar-weekdays"],
                    child=[
                        Widget.Label(label="Mo"),
                        Widget.Label(label="Tu"),
                        Widget.Label(label="We"),
                        Widget.Label(label="Th"),
                        Widget.Label(label="Fr"),
                        Widget.Label(label="Sa"),
                        Widget.Label(label="Su"),
                    ]
                ),
                self.days_grid
            ]
        )

        self.update_calendar()

    def _create_header(self):
        return Widget.Box(
            css_classes=["calendar-header"],
            child=[
                Widget.Button(
                    child=Widget.Icon(image="pan-start-symbolic"),
                    on_click=lambda x: self.prev_month(),
                    css_classes=["calendar-nav-button"]
                ),
                Widget.Label(
                    css_classes=["calendar-month-year"],
                    label=self.date.strftime("%B %Y")
                ),
                Widget.Button(
                    child=Widget.Icon(image="pan-end-symbolic"),
                    on_click=lambda x: self.next_month(),
                    css_classes=["calendar-nav-button"]
                )
            ]
        )

    def _create_days_grid(self):
        return Widget.Grid(
            css_classes=["calendar-days"],
            column_num=7
        )

    def update_calendar(self):
        self.header.child[1].label = self.date.strftime("%B %Y")
        grid_children = []

        # Определяем первый день месяца и количество дней
        first_day = datetime.date(self.date.year, self.date.month, 1)
        days_in_month = (datetime.date(self.date.year, self.date.month % 12 + 1, 1) -
                        datetime.timedelta(days=1)).day if self.date.month < 12 else 31

        # Определяем, с какого дня недели начинается месяц (0 = понедельник, 6 = воскресенье)
        first_weekday = first_day.weekday()

        # Добавляем пустые ячейки для выравнивания
        for _ in range(first_weekday):
            grid_children.append(Widget.Label(label=""))

        for day in range(1, days_in_month + 1):
            current_date = datetime.date(self.date.year, self.date.month, day)
            is_today = current_date == self.today
            is_selected = current_date == self.selected_date

            day_button = Widget.Button(
                child=Widget.Label(label=str(day)),
                css_classes=["calendar-day"],
                on_click=lambda x, d=day: self.select_day(d)
            )

            if is_today:
                day_button.add_css_class("today")
            if is_selected:
                day_button.add_css_class("selected")

            grid_children.append(day_button)

        self.days_grid.child = grid_children

    def prev_month(self):
        year = self.date.year - 1 if self.date.month == 1 else self.date.year
        month = 12 if self.date.month == 1 else self.date.month - 1
        self.date = datetime.datetime(year, month, 1)
        self.update_calendar()

    def next_month(self):
        year = self.date.year + 1 if self.date.month == 12 else self.date.year
        month = 1 if self.date.month == 12 else self.date.month + 1
        self.date = datetime.datetime(year, month, 1)
        self.update_calendar()

    def select_day(self, day):
        self.selected_date = datetime.date(self.date.year, self.date.month, day)
        self.update_calendar()

def calendar_window():
    return Widget.Window(
        namespace="ignis_CALENDAR",
        anchor=["top", 'right'],
        layer="top",
        visible=False,
        css_classes=["calendar-window"],
        child=Calendar()
    )
