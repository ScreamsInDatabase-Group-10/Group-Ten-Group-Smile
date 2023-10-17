from textual.app import ComposeResult
from textual.widgets import Placeholder
from textual.containers import Container
from util import ContextWidget


class BooksPanel(ContextWidget):
    def compose(self) -> ComposeResult:
        yield Container(
            Placeholder("Search Bar", id="book-search-section", classes="panel-sections book-search"),
            Placeholder("Book Results", id="book-results-section", classes="panel-sections book-results"),
            classes="panel books",
            id="app-panel-books",
        )
