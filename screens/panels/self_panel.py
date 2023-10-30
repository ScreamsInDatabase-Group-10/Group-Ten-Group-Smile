from textual.app import ComposeResult
from textual.widgets import Placeholder, Label, Static, DataTable, ContentSwitcher, Button
from textual.containers import Container, Horizontal
from util import ContextWidget



class ConnectionsPanel(Static):
    def compose(self) -> ComposeResult:
        with Horizontal(id="buttons"):
            yield Button("Following", id="following-table")
            yield Button("Followers", id="follower-table")
        with ContentSwitcher(initial="following-table"):
            yield DataTable(id="following-table")
            yield DataTable(id="follower-table")

class SelfPanel(ContextWidget):
    def compose(self) -> ComposeResult:
        user = self.context.logged_in
        yield Container(
            Static("Email: " + user.email + " Name: " + user.name_first + " " + user.name_last + "\nDate Created: " + user.creation_dt.strftime('%b %d %Y')
                   , id="user-info-section", classes="panel-sections user-info"),
            Placeholder("Collections", id="collections-section", classes="panel-sections collections"),
            ConnectionsPanel(),
            classes="panel self",
            id="app-panel-self",
        )

