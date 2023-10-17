from textual.app import ComposeResult
from textual.widgets import Placeholder
from textual.containers import Container
from util import ContextWidget


class UsersPanel(ContextWidget):
    def compose(self) -> ComposeResult:
        yield Container(
            Placeholder("Search Bar", id="user-search-section", classes="panel-sections user-search"),
            Placeholder("User Results", id="user-results-section", classes="panel-sections user-results"),
            classes="panel users",
            id="app-panel-users",
        )
