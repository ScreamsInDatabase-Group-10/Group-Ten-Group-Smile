from rich.console import RenderableType
from textual.widget import Widget
from textual.screen import Screen, ModalScreen
from textual.widgets import Static
from .context import ApplicationContext

"""
SUMMARY:
Some base classes to inject ApplicationContext into widget classes
Mostly just makes type inference easier, it would work without these.
"""


class ContextWidget(Widget):
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
        self.context: ApplicationContext = self.app.context


class ContextScreen(Screen):
    def __init__(self, name=None, id=None, classes=None) -> None:
        super().__init__(name, id, classes)
        self.context: ApplicationContext = self.app.context


class ContextModal(ModalScreen):
    def __init__(
        self, name: str | None = None, id: str | None = None, classes: str | None = None
    ) -> None:
        super().__init__(name, id, classes)
        self.context: ApplicationContext = self.app.context


class ContextStatic(Static):
    def __init__(
        self,
        renderable: RenderableType = "",
        *,
        expand: bool = False,
        shrink: bool = False,
        markup: bool = True,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False
    ) -> None:
        super().__init__(
            renderable,
            expand=expand,
            shrink=shrink,
            markup=markup,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
        )
        self.context: ApplicationContext = self.app.context
