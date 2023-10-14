from textual.widget import Widget
from textual.app import App
from .context import ApplicationContext

class ContextWidget(Widget):
    def __init__(self, *children: Widget, name: str | None = None, id: str | None = None, classes: str | None = None, disabled: bool = False) -> None:
        super().__init__(*children, name=name, id=id, classes=classes, disabled=disabled)
        self.context: ApplicationContext = self.app.context