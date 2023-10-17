from textual.app import ComposeResult
from textual.widgets import Placeholder
from textual.containers import Container
from util import ContextWidget


class SelfPanel(ContextWidget):
    def compose(self) -> ComposeResult:
        yield Container(
            Placeholder("Self Panel"),
            classes="panel self",
            id="app-panel-self",
        )
