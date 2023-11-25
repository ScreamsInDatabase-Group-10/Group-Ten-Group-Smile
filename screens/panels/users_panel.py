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


class UserActionsModal(ContextModal):
    def __init__(
        self,
        record: UserRecord,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name, id, classes)
        self.record = record
        cursor = self.context.db.execute(
            "SELECT user_id from users_following where user_id=%s AND following_id=%s",
            [self.context.logged_in.id, record.id],
        )
        if cursor.fetchone():
            self.following = True
        else:
            self.following = False
        cursor.close()

    def compose(self) -> ComposeResult:
        with Grid(id="user-actions-divider"):
            yield Static(
                f"[b]User Actions:[/b] [i]{self.record.name_first} {self.record.name_last}[/i]",
                id="actions-title",
            )
            if self.following:
                yield Button("Unfollow", id="follow-user-button")
            else:
                yield Button("Follow", id="follow-user-button")

            yield Button("Exit", id="exit-user-actions")

    @on(Button.Pressed, "#exit-user-actions")
    def exit_actions(self):
        self.dismiss()

    @on(Button.Pressed, "#follow-user-button")
    def follow(self):
        try:
            if self.following:
                self.context.db.execute(
                    "DELETE FROM users_following where user_id = %s AND following_id = %s",
                    [self.context.logged_in.id, self.record.id],
                )
            else:
                self.context.db.execute(
                    "INSERT INTO users_following (user_id, following_id) VALUES (%s, %s)",
                    [self.context.logged_in.id, self.record.id],
                )
            self.context.db.commit()
            self.app.notify("Success!", severity="information")
            self.dismiss()
        except:
            self.app.notify("Failure", severity="error")


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
        self.fields: SearchFields = {}

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
                cursor_type="row",
            ),
            classes="panel users",
            id="app-panel-users",
        )

    def search_update(self, values: Union[SearchFields, None]):
        self.query_one("#user-search-main", expect_type=Input).value = (
            values if values else dict()
        ).get("name_first", "")
        self.fields = values if values else dict()
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

    @on(PaginatedTable.CursorEvent)
    def on_row_highlight(self, event: PaginatedTable.CursorEvent):
        self.app.push_screen(UserActionsModal(event.value, id="user-actions-modal"))
