from textual.app import ComposeResult
from textual.widgets import Placeholder, Label, Static, DataTable, ContentSwitcher, Button, TabbedContent, TabPane
from textual.containers import Container, Horizontal
from util import ContextWidget
from util.pagination import PaginatedTable
from app_types.user import UserRecord




class ConnectionsPanel(Static):
    def compose(self) -> ComposeResult:
        with TabbedContent(id="account_connections"):
            with TabPane("Following", id="following"):
                yield PaginatedTable(
                    UserRecord,
                    [
                        {
                            "key": "id",
                            "name": "User Id",
                            "render": lambda id: str(id),
                            "sort_by": "id",
                        },
                        {
                            "key": "name_first",
                            "name": "First Name",
                            "render": lambda name: name,
                            "sort_by": "name_first",
                        },
                        {
                            "key": "name_last",
                            "name": "Last Name",
                            "render": lambda name: name,
                            "sort_by": "name_last",
                        },
                        {
                            "key": "creation_dt",
                            "name": "Creation Date",
                            "render": lambda dt: dt.strftime("%b %d, %Y"),
                        },
                        {
                            "key": "email",
                            "name": "Email",
                            "render": lambda email: email,
                        },
                    ],
                    id="user-results-section",
                    classes="panel-selections user-results",
                    initial_params={},
                    initial_pagination={
                        "limit": 25,
                        "offset": 0,
                        "order": [["name_first", "ASC"], ["name_last", "ASC"]],
                    },
                )
            with TabPane("Followers", id="followers"):
                yield PaginatedTable(
                    UserRecord,
                    [
                        {
                            "key": "id",
                            "name": "User Id",
                            "render": lambda id: str(id),
                            "sort_by": "id",
                        },
                        {
                            "key": "name_first",
                            "name": "First Name",
                            "render": lambda name: name,
                            "sort_by": "name_first",
                        },
                        {
                            "key": "name_last",
                            "name": "Last Name",
                            "render": lambda name: name,
                            "sort_by": "name_last",
                        },
                        {
                            "key": "creation_dt",
                            "name": "Creation Date",
                            "render": lambda dt: dt.strftime("%b %d, %Y"),
                        },
                        {
                            "key": "email",
                            "name": "Email",
                            "render": lambda email: email,
                        },
                    ],
                    id="user-results-section",
                    classes="panel-selections user-results",
                    initial_params={},
                    initial_pagination={
                        "limit": 25,
                        "offset": 0,
                        "order": [["name_first", "ASC"], ["name_last", "ASC"]],
                    },
                )






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

