from textual.app import ComposeResult
from textual.widgets import Placeholder, Label, Static, ListView, ListItem, Button
from textual.containers import Container
from app_types.user import CollectionRecord, UserRecord
from util import ContextWidget

def CollectionContainer(user: UserRecord) -> Container:
    # TODO: make container fill all the way down
    if(len(user.collections()) == 0):
        return Container(
                Static("Collections"),
                Static("No user collections! Make your first one below!")
            )
    return Container(
                Static("Collections"),
                ListView(
                    *[ListItem(Collection(c)) for c in user.collections()]
                )
            )

class Collection(Static):
    def __init__(
            self,
            collection: CollectionRecord,
            name: str | None = None,
            id: str | None = None,
            classes: str | None = None,
            disabled: bool = False,

    ):
        super().__init__(
            name=name, id=id, classes=classes, disabled=disabled
        )
        self.collection = collection

    def compose(self) -> ComposeResult:
        yield Static(self.collection.name)
        yield Button("Edit", id=f"collection-button-{self.collection.id}")

class SelfPanel(ContextWidget):
    def compose(self) -> ComposeResult:
        user = self.context.logged_in
        yield Container(
            Static("Email: " + user.email + " Name: " + user.name_first + " " + user.name_last + "\nDate Created: " + user.creation_dt.strftime('%b %d %Y')
                   , id="user-info-section", classes="panel-sections user-info"),
            CollectionContainer(user),
            Placeholder("Connections", id="connections-section", classes="panel-sections connections"),
            classes="panel self",
            id="app-panel-self",
        )
