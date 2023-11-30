from textual import on
from textual.app import ComposeResult
from textual.events import Show
from textual.widget import Widget
from textual.widgets import (
    Placeholder,
    Label,
    Static,
    TabbedContent,
    TabPane,
    DataTable,
    ListView,
    ListItem,
    Button,
    Input,
    Rule
)
from textual.containers import Container, Grid
from textual import work, on
from textual.reactive import reactive
from app_types.book import BookRecord
from app_types.user import CollectionRecord, UserRecord
from util.widget import ContextModal
from util import ContextWidget


class ConnectionsPanel(ContextWidget):
    followers: reactive[list[UserRecord]] = reactive([])
    following: reactive[list[UserRecord]] = reactive([])

    @work(thread=True)
    async def load_followers(self):
        self.followers = self.context.logged_in.followers

    @work(thread=True)
    async def load_following(self):
        self.following = self.context.logged_in.following

    def on_mount(self):
        self.load_followers()
        self.load_following()
        self.query_one("#table-followers", expect_type=DataTable).add_columns(
            "First Name", "Last Name", "Email"
        )
        self.query_one("#table-following", expect_type=DataTable).add_columns(
            "First Name", "Last Name", "Email", "Unfollow Button"
        )

    def watch_followers(self, old, new: list[UserRecord]):
        table = self.query_one("#table-followers", expect_type=DataTable)
        table.clear()
        table.add_rows([(i.name_first, i.name_last, i.email) for i in new])

    def watch_following(self, old, new):
        table = self.query_one("#table-following", expect_type=DataTable)
        table.clear()
        table.add_rows(
            [(i.name_first, i.name_last, i.email, "[b]Unfollow[/b]")
             for i in new]
        )

    def compose(self) -> ComposeResult:
        with TabbedContent():
            with TabPane("Followers"):
                yield DataTable(id="table-followers")
            with TabPane("Following"):
                yield DataTable(id="table-following")

    @on(DataTable.CellHighlighted, selector="#table-following")
    def handle_kill_click(self, event: DataTable.CellHighlighted):
        if event.value == "[b]Unfollow[/b]":
            record: UserRecord = self.following[event.coordinate.row]
            self.context.db.execute(
                "DELETE FROM users_following WHERE user_id = %s AND following_id = %s",
                [self.context.logged_in.id, record.id],
            )
            self.context.db.commit()
            del self.following[event.coordinate.row]
            self.watch_following([], self.following)

    @on(Show)
    def refresh_following(self):
        self.load_followers()
        self.load_following()


class CollectionContainer(ContextWidget):
    def compose(self) -> ComposeResult:
        with TabbedContent():
            with TabPane("Collections"):
                yield Button("Create Collection", id="create-collection-button")
                yield ListView(
                    *[
                        ListItem(Collection(c), classes="list-item")
                        for c in self.context.logged_in.collections()
                    ],
                    id="collection-list",
                )

    @on(Button.Pressed, "#create-collection-button")
    def create_collection_button(self):
        self.query_one("#collection-list", expect_type=ListView).mount(
            ListItem(
                Collection(
                    CollectionRecord.create(
                        self.context.orm, "New Collection", self.context.logged_in
                    )
                )
            )
        )


class CollectionEditModal(ContextModal):
    def __init__(
        self,
        collection: "CollectionRecord",
        name: str | None = None,
        id: str | None = None,
        classes: str | None = "collection-edit-modal",
    ) -> None:
        super().__init__(name, id, classes)
        self.collection = collection
        self.collection.books = self.collection._init_books()  # refresh book list
        self.newName = collection.name

    def compose(self) -> ComposeResult:
        with Grid(id="collection-edit-modal-container"):
            yield Static(
                f'[b]Edit Collection: "{self.collection.name}"[/b]', id="edit-title"
            )
            yield Static(
                f"[b]Book Count:[/b] {self.collection.book_count}",
                classes="collection-info",
            )
            yield Static(
                f"[b]Page Count:[/b] {self.collection.page_count}",
                classes="collection-info",
            )
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
                *[
                    ListItem(CollectionBook(b, self.collection),
                             classes="list-item")
                    for b in self.collection.books
                ],
                id="book-list",
            )
            yield Button("Save", id="save-button")
            yield Button("Delete", id="delete-button")
            yield Button("Cancel", id="cancel-button")

    @on(Button.Pressed, "#save-button")
    def on_save(self):
        self.collection.name = self.newName
        self.collection.save()
        self.dismiss(self.collection)

    @on(Button.Pressed, "#delete-button")
    def on_delete(self):
        self.collection.delete()
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
        if self.removed == False:
            # TODO: Change button title to red strikethrough
            self.query_one("#title", expect_type=Static).update(
                f"[s]{self.book.title}[/s]"
            )
            self.query_one("#toggle-button", expect_type=Button).label = "Add"
            self.removed = True
            self.collection.remove_book(self.book)
        else:
            self.query_one("#title", expect_type=Static).update(
                self.book.title)
            self.query_one("#toggle-button",
                           expect_type=Button).label = "Remove"
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
        if collection == None:
            return
        if collection.deleted:
            self.remove()
        else:
            self.collection = collection
            self.query_one("#collection-name", expect_type=Static).update(
                self.collection.name
            )

    @on(Button.Pressed, "#collection-button")
    def on_edit(self):
        self.app.push_screen(
            CollectionEditModal(self.collection), self.collection_update
        )


class SelfPanel(ContextWidget):
    def on_mount(self):
        table = self.query_one("#top-ten-data", expect_type=DataTable)
        table.add_columns("Title", "Authors", "Average Rating")
        self.get_table_data()
        self.update_user_data()
        
    @work(thread=True)
    async def update_user_data(self):
        user = self.context.logged_in
        email = user.email
        name = user.name_first + " " + user.name_last
        created = user.creation_dt
        
        count_collections = self.context.db.execute("SELECT COUNT(collection_id) FROM users_collections WHERE user_id = %s", [user.id]).fetchone()[0]
        count_following = self.context.db.execute("SELECT COUNT(following_id) FROM users_following WHERE user_id = %s", [user.id]).fetchone()[0]
        count_followers = self.context.db.execute("SELECT COUNT(user_id) FROM users_following WHERE following_id = %s", [user.id]).fetchone()[0]
        
        await self.query_one("#user-info-section", expect_type=Static).remove()
        await self.query_one("#app-panel-self", expect_type=Container).mount(Static(
                f"""Name: {name}
Email: {email}
Created On: {user.creation_dt.strftime("%b %d %Y")}

Collections: {count_collections}
Following: {count_following}
Followers: {count_followers}""",
                id="user-info-section",
                classes="panel-sections user-info",
            ), before="#collections-section")
        

    @work(thread=True)
    def get_table_data(self):
        data = [BookRecord._from_search(self.context.db, "books", self.context.orm, *record) for record in self.context.db.execute(
            "SELECT * FROM view_books WHERE id IN (SELECT book_id FROM users_ratings WHERE user_id = %s) ORDER BY avg_rating DESC LIMIT 10", [self.context.logged_in.id])]

        table = self.query_one("#top-ten-data", expect_type=DataTable)
        table.clear()
        table.add_rows([[i.title if len(i.title) <= 50 else i.title[:47] + "...", ", ".join([x.name for x in i.authors]), str(
            i.avg_rating if i.avg_rating else 0)] for i in data])

    def compose(self) -> ComposeResult:
        yield Container(
            Static(
                """Name: 
Email: 
Created On: 

Collections: 
Following: 
Followers: """,
                id="user-info-section",
                classes="panel-sections user-info",
            ),
            CollectionContainer(id="collections-section"),
            ConnectionsPanel(id="connections-section"),
            Container(
                Rule(),
                DataTable(id="top-ten-data"),
                id="top-ten"
            ),
            classes="panel self",
            id="app-panel-self",
        )

    # @on(Button.Pressed, "create-button")
    # def on_create_collection():
