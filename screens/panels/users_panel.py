from typing import TypedDict, Union
from textual import on
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static, Button, Input, ListView, Label, ListItem
from textual.containers import Grid, Horizontal, Container, VerticalScroll
from app_types.user import UserRecord
from util import ContextWidget
from util.pagination import PaginatedTable
from util.widget import ContextModal


class SearchFields(TypedDict):
    first_name: str
    last_name: str
    email: str
    id: str


class AdvancedSearchModal(ContextModal):
    def __init__(
        self,
        field_values: SearchFields,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = "advanced-search-modal",
    ) -> None:
        super().__init__(name, id, classes)
        self.fields = field_values

    def compose(self) -> ComposeResult:
        with Grid(id="advanced-search-modal-container"):
            yield Static("[b]Advanced Search[/b]", id="advanced-title")
            yield ListItem(
                Static("[b]First Name[/b]"),
                classes="input-label",
                id="label-name-first",
            )
            yield Input(
                value=self.fields.get("first_name", ""),
                placeholder="First Name",
                classes="input-field",
                id="input-first-name",
                name="name_first",
            )
            yield ListItem(
                Static("[b]Last Name[/b]"), classes="input-label", id="label-name-last"
            )
            yield Input(
                value=self.fields.get("last_name", ""),
                placeholder="Last Name",
                classes="input-field",
                id="input-last-name",
                name="name_last",
            )
            yield ListItem(
                Static("[b]Email[/b]"), classes="input-label", id="label-email"
            )
            yield Input(
                value=self.fields.get("email", ""),
                placeholder="Email",
                classes="input-field",
                id="input-email",
                name="email",
            )
            yield ListItem(Static("[b]ID[/b]"), classes="input-label", id="label-id")
            yield Input(
                value=self.fields.get("id", ""),
                placeholder="ID",
                classes="input-field",
                id="input-id",
                name="id",
            )
            with Container(id="advanced-controls"):
                yield Button("Cancel", classes="advanced-control", id="button-cancel")
                yield Button("Search", classes="advanced-control", id="button-search")

    @on(Button.Pressed, "#button-cancel")
    def on_cancel(self, _event: Button.Pressed):
        self.dismiss(None)

    @on(Button.Pressed, "#button-search")
    def on_search(self, _event: Button.Pressed):
        self.dismiss(self.fields)

    @on(Input.Changed)
    def on_input(self, event: Input.Changed):
        if event.validation_result == None or event.validation_result.is_valid:
            if len(event.value) == 0 and event.input.name in self.fields.keys():
                del self.fields[event.input.name]
            else:
                self.fields[event.input.name] = event.value


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
        self.query_one("#user-search-main", expect_type=Input).value = values.get(
            "name_first", ""
        )
        self.fields = values
        transformed_values = {}
        for k, v in self.fields.items():
            if k == "id":
                transformed_values[k] = int(v)
            else:
                transformed_values[k] = v

        self.query_one("#user-results-section", expect_type=PaginatedTable).search(
            transformed_values
        )

    @on(Button.Pressed, "#btn-user-search")
    def on_search(self):
        self.search_update(self.fields)

    @on(Button.Pressed, "#btn-user-advanced")
    def on_advanced(self):
        self.app.push_screen(AdvancedSearchModal(self.fields), self.search_update)

    @on(Input.Changed, "#user-search-main")
    def on_search_change(self, event: Input.Changed):
        if len(event.value) == 0 and "name_first" in self.fields.keys():
            del self.fields["name_first"]
        else:
            self.fields["name_first"] = event.value
