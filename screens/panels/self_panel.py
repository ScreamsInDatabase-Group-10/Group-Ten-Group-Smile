from textual import on
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Placeholder, Label, Static, ListView, ListItem, Button, Input
from textual.containers import Container, Grid
from app_types.book import BookRecord
from app_types.user import CollectionRecord, UserRecord
from util import ContextWidget
from util.widget import ContextModal


def CollectionContainer(user: UserRecord) -> Container:
    # TODO: make container fill all the way down
    if (len(user.collections()) == 0):
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


class CollectionEditModal(ContextModal):
    def __init__(
        self,
        collection: "Collection",
        name: str | None = None,
        id: str | None = None,
        classes: str | None = "advanced-search-modal",
    ) -> None:
        super().__init__(name, id, classes)
        self.collection = collection

    def compose(self) -> ComposeResult:
        with Grid(id="collection-edit-modal-container"):
            yield Static("[b]Edit Collection:[/b]", id="edit-title")
            yield ListItem(
                Static("[b]Name[/b]"), classes="input-label", id="label-name"
            )
            yield Input(
                value=self.collection.name,
                placeholder="Collection Title",
                classes="input-field",
                id="input-name",
                name="name",
            )
            yield ListView(
                *[ListItem(CollectionBook(b, self.collection)) for b in self.collection.books]
            )
            yield Button("Save", id="save-button")
            yield Button("Close", id="close-button")

    @on(Button.Pressed, "#save-button")
    def on_save(self):
        self.collection.save()

    @on(Button.Pressed, "#close-button")
    def on_close(self):
        self.dismiss(None)


class CollectionBook(Static):
    def __init__(
            self,
            book: BookRecord,
            collection: CollectionRecord,
            name: str | None = None,
            id: str | None = None,
            classes: str | None = None,
            disabled: bool = False,
    ):
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)
        self.book = book
        self.collection = collection
        self.removed = False

    def compose(self) -> ComposeResult:
        yield Static(self.book.title, id="title")
        yield Button("Remove", id="toggle-button")

    @on(Button.Pressed, "#toggle-button")
    def on_remove(self):
        if (self.removed == False):
            # TODO: Change button title to red strikethrough
            self.removed = True
            # TODO: remove book from collection in db.
            # Maybe a collection.removeBook method
        else:
            # TODO: add the book back to the collection
            self.removed = False


class Collection(Static):
    def __init__(
            self,
            collection: CollectionRecord,
            name: str | None = None,
            id: str | None = None,
            classes: str | None = None,
            disabled: bool = False,

    ):
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)
        self.collection = collection

    def compose(self) -> ComposeResult:
        yield Static(self.collection.name)
        yield Button("View/Edit", id="collection-button")

    @on(Button.Pressed, "#collection-button")
    def on_edit(self):
        # TODO: self.collection is confirmed to be correct. Finish function
        self.app.push_screen(CollectionEditModal(self.collection))


class SelfPanel(ContextWidget):
    def compose(self) -> ComposeResult:
        user = self.context.logged_in
        yield Container(
            Static("Email: " + user.email + " Name: " + user.name_first + " " + user.name_last + "\nDate Created: " +
                   user.creation_dt.strftime('%b %d %Y'), id="user-info-section", classes="panel-sections user-info"),
            CollectionContainer(user),
            Placeholder("Connections", id="connections-section",
                        classes="panel-sections connections"),
            classes="panel self",
            id="app-panel-self",
        )
