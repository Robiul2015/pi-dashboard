from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Header, Footer, Label, ListView, ListItem
from services.notion_service import NotionService
from services.calendar_service import CalendarService
from services.buzzer_service import BuzzerService
from services.touch_service import start_touch_listener
import asyncio


class DashboardApp(App):
    """A Textual productivity dashboard."""

    CSS_PATH = "dashboard.tcss"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh Data")
    ]

    def __init__(self):
        super().__init__()
        self.notion = NotionService()
        self.calendar = CalendarService()
        self.buzzer = BuzzerService()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="dashboard-grid"):
            with Vertical(classes="box", id="goals-box"):
                yield Label("🎯 DAILY GOALS", classes="section-title")
                yield ListView(id="goals-list")

            with Vertical(classes="box", id="calendar-box"):
                yield Label("📅 UPCOMING EVENTS", classes="section-title")
                yield ListView(id="calendar-list")

        yield Footer()

    async def on_mount(self) -> None:
        """Called when app starts."""
        self.call_after_refresh(self.action_refresh)
        self.set_interval(300, self.action_refresh)
        self.set_interval(30, self._check_alarms)
        start_touch_listener(callback=lambda: self.call_from_thread(self.action_refresh))

    async def action_refresh(self) -> None:
        """Fetch all data asynchronously and update UI."""
        self.query_one("#calendar-list").clear()
        self.query_one("#goals-list").clear()

        calendar_events, goals = await asyncio.gather(
            self.calendar.get_upcoming_events(),
            self.notion.get_goals()
        )

        for event in calendar_events:
            self.query_one("#calendar-list").append(ListItem(Label(event)))

        for goal in goals:
            self.query_one("#goals-list").append(ListItem(Label(goal)))

    async def _check_alarms(self) -> None:
        """Check cached alarm data — no extra API call."""
        alarms = self.notion.get_cached_alarms()
        await self.buzzer.check_alarms(alarms)

    async def on_unmount(self) -> None:
        """Clean up GPIO on exit."""
        self.buzzer.cleanup()
