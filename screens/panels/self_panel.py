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
            Static("No user collections! Make your first one below!"),
            id="collection-container"
        )
    return Container(
        Static("Collections"),
        ListView(
            *[ListItem(Collection(c), classes="list-item") for c in user.collections()]
        ),
        id="colleciton-container"
    )


class CollectionEditModal(ContextModal):
    def __init__(
        self,
        collection: "Collection",
        name: str | None = None,
        id: str | None = None,
        classes: str | None = "collection-edit-modal",
    ) -> None:
        super().__init__(name, id, classes)
        self.collection = collection
        self.newName = collection.name

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
                *[ListItem(CollectionBook(b, self.collection), classes="list-item") for b in self.collection.books],
                id="book-list"
            )
            yield Button("Save", id="save-button")
            yield Button("Cancel", id="cancel-button")

    @on(Button.Pressed, "#save-button")
    def on_save(self):
        self.collection.name = self.newName
        self.collection.save()
        self.dismiss(self.collection)

    @on(Button.Pressed, "#cancel-button")
    def on_close(self):
        self.dismiss(None)
    
    def on_input_changed(self, event: Input.Changed):
        self.newName = event.input.value


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
            self.query_one("#title", expect_type=Static).update(
                f"[s]{self.book.title}[/s]")
            self.query_one("#toggle-button", expect_type=Button).label = "Add"
            self.removed = True
            self.collection.remove_book(self.book)
        else:
            self.query_one("#title", expect_type=Static).update(self.book.title)
            self.query_one("#toggle-button", expect_type=Button).label = "Remove"
            self.collection.add_book(self.book)
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
        yield Static(self.collection.name, id="collection-name")
        yield Button("View/Edit", id="collection-button")

    def collection_update(self, collection: CollectionRecord | None) -> None:
        if collection == None: return
        self.collection = collection
        self.query_one("#collection-name", expect_type=Static).update(
            self.collection.name
            )

    @on(Button.Pressed, "#collection-button")
    def on_edit(self):
        self.app.push_screen(CollectionEditModal(self.collection), self.collection_update)


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
