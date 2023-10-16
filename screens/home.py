from textual.app import ComposeResult
from textual.widgets import Header, Footer
from util import ContextScreen

class HomeScreen(ContextScreen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()