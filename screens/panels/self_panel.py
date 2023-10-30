from textual.app import ComposeResult
from textual.widgets import Placeholder, Label, Static, ListView, ListItem
from textual.containers import Container
from util import ContextWidget

class SelfPanel(ContextWidget):
    def compose(self) -> ComposeResult:
        user = self.context.logged_in
        yield Container(
            Static("Email: " + user.email + " Name: " + user.name_first + " " + user.name_last + "\nDate Created: " + user.creation_dt.strftime('%b %d %Y')
                   , id="user-info-section", classes="panel-sections user-info"),
            ListView(
                *[ListItem(Static(c.name)) for c in user.collections()]
            ),
            Placeholder("Connections", id="connections-section", classes="panel-sections connections"),
            classes="panel self",
            id="app-panel-self",
        )
