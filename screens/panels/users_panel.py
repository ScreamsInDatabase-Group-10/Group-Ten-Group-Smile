from typing import TypedDict, Union
from textual import on
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Button, Input, ListView, Label, ListItem
from textual.containers import Horizontal, Container, VerticalScroll
from app_types.user import UserRecord
from util import ContextWidget
from util.pagination import PaginatedTable


class SearchFields(TypedDict):
    first_name: str
    last_name: str
    email: str
    id: str

class UsersPanel(ContextWidget):
    def __init__(
        self,
        *children: Widget,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        super().__init__(
            *children, name=name, id=id, classes=classes, disabled=disabled
        )
        self.fields = SearchFields = {}


    def compose(self) -> ComposeResult:
        yield Container(
            Horizontal(
                Input(value="", placeholder="Search Users", id="user-search-main"),
                Button("Search", id="btn-user-search"),
                Button("Advanced", id="btn-user-advanced"),
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

    def search_update(self, values: Union[SearchFields, None]):
        if values:
            self.query_one("#user-search-main", expect_type=Input).value = values.get("name_first", "")
            self.fields = values
            transformed_values = {}
            for k, v in self.fields.items():
                if k == "id":
                    transformed_values[k] = int(v)
                else:
                    transformed_values[k] = v
            
            self.query_one("#user-results-section", expect_type=PaginatedTable).search(transformed_values)
    
    @on(Button.Pressed, "#btn-user-search")
    def on_search(self):
        self.search_update(self.fields)

    @on(Input.Changed, "#user-search-main")
    def on_search_change(self, event: Input.Changed):
        if len(event.value) == 0 and "name_first" in self.fields.keys():
            del self.fields["name_first"]
        else:
            self.fields["name_first"] = event.value
