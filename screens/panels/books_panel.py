from textual.app import ComposeResult
from textual.widgets import Placeholder, Label
from textual.containers import Container
from util import ContextWidget
from textual.widget import Widget


class BooksPanel(Widget):
    def compose(self) -> ComposeResult:
        yield Placeholder("Books Panel", classes="panel-placeholder")
        yield Label("")
