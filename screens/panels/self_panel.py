from textual.app import ComposeResult
from textual.widgets import Placeholder
from textual.containers import Container
from util import ContextWidget


class SelfPanel(ContextWidget):
    def compose(self) -> ComposeResult:
        yield Container(
            Placeholder("User Info", id="user-info-section", classes="panel-sections user-info"),
            Placeholder("Collections", id="collections-section", classes="panel-sections collections"),
            Placeholder("Connections", id="connections-section", classes="panel-sections connections"),
            classes="panel self",
            id="app-panel-self",
        )
