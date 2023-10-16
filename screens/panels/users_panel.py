from textual.app import ComposeResult
from textual.widgets import Placeholder, Label
from textual.containers import Container
from util import ContextWidget
from textual.widget import Widget


class UsersPanel(Widget):
    def compose(self) -> ComposeResult:
        yield Placeholder("Users Panel", classes="panel-placeholder")
        yield Label("")
