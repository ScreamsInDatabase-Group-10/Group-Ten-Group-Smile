from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Placeholder, Label, Static, TabbedContent, TabPane, DataTable
from textual.containers import Container
from textual import work, on
from textual.reactive import reactive
from util import ContextWidget
from app_types import UserRecord

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
        self.query_one("#table-followers", expect_type=DataTable).add_columns("First Name", "Last Name", "Email")
        self.query_one("#table-following", expect_type=DataTable).add_columns("First Name", "Last Name", "Email", "Murder Button")

    def watch_followers(self, old, new: list[UserRecord]):
        table = self.query_one("#table-followers", expect_type=DataTable)
        table.clear()
        table.add_rows([(i.name_first, i.name_last, i.email) for i in new])

    def watch_following(self, old, new):
        table = self.query_one("#table-following", expect_type=DataTable)
        table.clear()
        table.add_rows([(i.name_first, i.name_last, i.email, "[b]KILL[/b]") for i in new])

    def compose(self) -> ComposeResult:
        with TabbedContent():
            with TabPane("Followers"):
                yield DataTable(id="table-followers")
            with TabPane("Following"):
                yield DataTable(id="table-following")

    @on(DataTable.CellHighlighted, selector="#table-following")
    def handle_kill_click(self, event: DataTable.CellHighlighted):
        if event.value == "[b]KILL[/b]":
            record: UserRecord = self.following[event.coordinate.row]
            self.context.db.execute("DELETE FROM users_following WHERE user_id = %s AND following_id = %s", [self.context.logged_in.id, record.id])
            del self.following[event.coordinate.row]
            self.watch_following([], self.following)


class SelfPanel(ContextWidget):
    def compose(self) -> ComposeResult:
        user = self.context.logged_in
        yield Container(
            Static("Email: " + user.email + " Name: " + user.name_first + " " + user.name_last + "\nDate Created: " + user.creation_dt.strftime('%b %d %Y')
                   , id="user-info-section", classes="panel-sections user-info"),
            Placeholder("Collections", id="collections-section", classes="panel-sections collections"),
            ConnectionsPanel(id="connections-section", classes="panel-sections connections"),
            classes="panel self",
            id="app-panel-self",
        )
