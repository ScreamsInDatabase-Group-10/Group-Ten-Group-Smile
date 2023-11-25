from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label
from util import ContextWidget
from textual.containers import Container


class RecommendationPanel(ContextWidget):
    def __init__(
        self,
        *children: Widget,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False
    ) -> None:
        super().__init__(
            *children, name=name, id=id, classes=classes, disabled=disabled
        )

    def compose(self) -> ComposeResult:
        yield Container(
            Label("test"),
            classes="panel rec",
            id="app-panel-rec",
        )
