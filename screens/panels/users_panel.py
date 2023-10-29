from textual.app import ComposeResult
from textual.widgets import Button, Input, ListView, Label, ListItem
from textual.containers import Horizontal, Container, VerticalScroll
from app_types.user import UserRecord
from util import ContextWidget
from util.pagination import PaginatedTable


class UsersPanel(ContextWidget):
    def compose(self) -> ComposeResult:
        yield Container(
            Horizontal(
                Input(value="", placeholder="Search Users", id="search-main"),
                Button("Search", id="btn-search"),
                Button("Advanced", id="btn-advanced"),
                id="user-search-section",
                classes="panel-sections users-search",
            ),
            PaginatedTable(
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
                        "render": lambda dt: dt,
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
            ),
            classes="panel users",
            id="app-panel-users",
        )
