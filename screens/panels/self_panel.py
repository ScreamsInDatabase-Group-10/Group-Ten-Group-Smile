from textual.app import ComposeResult
from textual.widgets import Placeholder, Label
from textual.containers import Container
from util import ContextWidget
from textual.widget import Widget


class SelfPanel(Widget):
    def compose(self) -> ComposeResult:
        yield Placeholder("Self Panel", classes="panel-placeholder")
        yield Label("")
