from textual.app import ComposeResult
from textual.widgets import Placeholder
from textual.containers import Container
from util import ContextWidget


class UsersPanel(ContextWidget):
    def compose(self) -> ComposeResult:
        yield Container(
            Placeholder("Users Panel"),
            classes="panel users",
            id="app-panel-users",
        )
