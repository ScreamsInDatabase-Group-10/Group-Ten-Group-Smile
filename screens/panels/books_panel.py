from textual.app import ComposeResult
from textual.widgets import Placeholder
from textual.containers import Container
from util import ContextWidget


class BooksPanel(ContextWidget):
    def compose(self) -> ComposeResult:
        yield Container(
            Placeholder("Books Panel"),
            classes="panel books",
            id="app-panel-books",
        )
