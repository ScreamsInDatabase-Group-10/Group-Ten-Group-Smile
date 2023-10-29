from typing import Any, Coroutine, Union
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Placeholder, Input, Button, Static, ListItem
from textual.containers import Container, Horizontal, Grid
from util import ContextWidget, PaginatedTable, ContextModal
from app_types import BookRecord
from datetime import datetime
from typing_extensions import TypedDict
from textual import on, work
from textual.suggester import Suggester
from textual.validation import Function
import difflib
from dateutil.parser import parse


class SearchFields(TypedDict):
    title: str
    min_length: int
    max_length: int
    edition: str
    released_after: datetime
    released_before: datetime
    isbn: int
    author_name: str
    publisher_name: str
    genre: str
    audience: str


class SearchSuggestions(Suggester):
    def __init__(self, *, use_cache: bool = True, case_sensitive: bool = False) -> None:
        super().__init__(use_cache=use_cache, case_sensitive=case_sensitive)
        self.possibilities = []

    def update(self, suggestions: list[str]):
        self.possibilities = suggestions

    async def get_suggestion(self, value: str) -> Coroutine[Any, Any, str | None]:
        matches = [
            i
            for i in difflib.get_close_matches(
                value, self.possibilities, cutoff=0.4, n=20
            )
            if i.lower().startswith(value.lower())
        ]
        return matches[0] if len(matches) > 0 else None


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
        self.genre_suggestions = SearchSuggestions()
        self.audience_suggestions = SearchSuggestions()
        self.load_audiences()
        self.load_genres()

    @work(exclusive=True, thread=True, group="adv-genre")
    def load_genres(self):
        cursor = self.context.db.execute("SELECT name FROM genres")
        self.genre_suggestions.update([r[0] for r in cursor.fetchall()])
        cursor.close()

    @work(exclusive=True, thread=True, group="adv-audience")
    def load_audiences(self):
        cursor = self.context.db.execute("SELECT name FROM audiences")
        self.audience_suggestions.update([r[0] for r in cursor.fetchall()])
        cursor.close()

    def compose(self) -> ComposeResult:
        with Grid(id="advanced-search-modal-container"):
            yield Static("[b]Advanced Search[/b]", id="advanced-title")
            yield ListItem(
                Static("[b]Title[/b]"), classes="input-label", id="label-title"
            )
            yield Input(
                value=self.fields.get("title", ""),
                placeholder="Book Title",
                classes="input-field",
                id="input-title",
                name="title",
            )
            yield ListItem(
                Static("[b]Length[/b]"), classes="input-label", id="label-length"
            )
            yield Input(
                value=self.fields.get("min_length", ""),
                placeholder="Min",
                classes="input-field small",
                id="input-length-min",
                name="min_length",
            )
            yield Input(
                value=self.fields.get("max_length", ""),
                placeholder="Max",
                classes="input-field small",
                id="input-length-max",
                name="max_length",
            )
            yield ListItem(
                Static("[b]Edition[/b]"), classes="input-label", id="label-edition"
            )
            yield Input(
                value=self.fields.get("edition", ""),
                placeholder="Edition Name",
                classes="input-field",
                id="input-edition",
                name="edition",
            )
            yield ListItem(
                Static("[b]Release Date[/b]"),
                classes="input-label",
                id="label-release-dt",
            )
            yield Input(
                value=self.fields.get("released_after", ""),
                placeholder="After",
                classes="input-field small",
                id="input-release-after",
                name="released_after",
                validators=[Function(self.check_date, "Value is an invalid date")],
            )
            yield Input(
                value=self.fields.get("released_before", ""),
                placeholder="Before",
                classes="input-field small",
                id="input-release-before",
                name="released_before",
                validators=[Function(self.check_date, "Value is an invalid date")],
            )
            yield ListItem(
                Static("[b]ISBN[/b]"), classes="input-label", id="label-isbn"
            )
            yield Input(
                value=self.fields.get("isbn", ""),
                placeholder="ISBN (Exact)",
                classes="input-field",
                id="input-isbn",
                name="isbn",
            )
            yield ListItem(
                Static("[b]Author[/b]"), classes="input-label", id="label-author"
            )
            yield Input(
                value=self.fields.get("author_name", ""),
                placeholder="Author Name",
                classes="input-field",
                id="input-author",
                name="author_name",
            )
            yield ListItem(
                Static("[b]Publisher[/b]"), classes="input-label", id="label-publisher"
            )
            yield Input(
                value=self.fields.get("publisher_name", ""),
                placeholder="Publisher Name",
                classes="input-field",
                id="input-publisher",
                name="publisher_name",
            )
            yield ListItem(
                Static("[b]Genre[/b]"), classes="input-label", id="label-genre"
            )
            yield Input(
                value=self.fields.get("genre", ""),
                placeholder="Genre",
                classes="input-field",
                id="input-genre",
                name="genre",
                suggester=self.genre_suggestions,
            )
            yield ListItem(
                Static("[b]Audience[/b]"), classes="input-label", id="label-audience"
            )
            yield Input(
                value=self.fields.get("audience", ""),
                placeholder="Audience",
                classes="input-field",
                id="input-audience",
                name="audience",
                suggester=self.audience_suggestions,
            )
            with Container(id="advanced-controls"):
                yield Button("Cancel", classes="advanced-control", id="button-cancel")
                yield Button("Search", classes="advanced-control", id="button-search")

    @on(Button.Pressed, "#button-cancel")
    def on_cancel(self, event: Button.Pressed):
        self.dismiss(None)

    @on(Button.Pressed, "#button-search")
    def on_search(self, event: Button.Pressed):
        self.dismiss(self.fields)

    def check_date(self, value: str) -> bool:
        if len(value) == 0:
            return True
        try:
            parse(value)
            return True
        except:
            return False

    @on(Input.Changed)
    def on_input(self, event: Input.Changed):
        if event.validation_result == None or event.validation_result.is_valid:
            if len(event.value) == 0 and event.input.name in self.fields.keys():
                del self.fields[event.input.name]
            else:
                self.fields[event.input.name] = event.value

class BookActionsModal(ContextModal):
    def __init__(self, record: BookRecord, name: str | None = None, id: str | None = None, classes: str | None = None) -> None:
        super().__init__(name, id, classes)
        self.record = record

    def check_date(self, value: str) -> bool:
        if len(value) == 0:
            return True
        try:
            parse(value)
            return True
        except:
            return False

    def compose(self) -> ComposeResult:
        with Grid(id="book-actions-divider"):
            yield Static(f"[b]Book Actions:[/b] [i]{self.record.title}[/i]", id="actions-title")
            with Grid(id="modal-section-sessions", classes="modal-section"):
                yield Static("New Read Session", classes="section-title")
                yield ListItem(
                    Static("[b]Start Time[/b]"), classes="input-label", id="label-start-time"
                )
                yield Input(
                    value="",
                    placeholder="Start Time",
                    classes="input-field",
                    id="input-start-time",
                    validators=[Function(self.check_date, "Value is an invalid date")]
                )
                yield ListItem(
                    Static("[b]End Time[/b]"), classes="input-label", id="label-end-time"
                )
                yield Input(
                    value="",
                    placeholder="End Time",
                    classes="input-field",
                    id="input-end-time",
                    validators=[Function(self.check_date, "Value is an invalid date")]
                )
                yield ListItem(
                    Static("[b]Start Page[/b]"), classes="input-label", id="label-start-page"
                )
                yield Input(
                    value="",
                    placeholder="Start Page",
                    classes="input-field",
                    id="input-start-page",
                )
                yield ListItem(
                    Static("[b]End Time[/b]"), classes="input-label", id="label-end-page"
                )
                yield Input(
                    value="",
                    placeholder="End Page",
                    classes="input-field",
                    id="input-end-page",
                )
                yield Button("Create", id="create-session")
            yield Button("Exit", id="exit-actions")
    
    @on(Button.Pressed, "#exit-actions")
    def exit_actions(self):
        self.dismiss()

    @on(Button.Pressed, "#create-session")
    def create_session(self):
        inputs: dict[str, Input] = {
            "start_time": self.query_one("#input-start-time", expect_type=Input),
            "end_time": self.query_one("#input-end-time", expect_type=Input),
            "start_page": self.query_one("#input-start-page", expect_type=Input),
            "end_page": self.query_one("#input-end-page", expect_type=Input)
        }
        if not all([(i.validate(i.value) == None or i.validate(i.value).is_valid) and len(i.value) > 0 for i in inputs.values()]):
            return
        
        try:
            values = {k:v.value for k, v in inputs.items()}
            self.context.db.execute("INSERT INTO users_sessions (session_id, book_id, user_id, start_datetime, end_datetime, start_page, end_page) VALUES (%s, %s, %s, %s, %s, %s, %s)", [
                self.context.orm.next_available_id("users_sessions", col="session_id"),
                self.record.id,
                self.context.logged_in.id,
                parse(values["start_time"]),
                parse(values["end_time"]),
                int(values["start_page"]),
                int(values["end_page"])
            ])
            self.context.db.commit()
            self.app.notify("Success!", severity="information")
        except:
            self.app.notify("Failure", severity="error")
        self.query_one("#input-start-time", expect_type=Input).value = ""
        self.query_one("#input-end-time", expect_type=Input).value = ""
        self.query_one("#input-start-page", expect_type=Input).value = ""
        self.query_one("#input-end-page", expect_type=Input).value = ""


class BooksPanel(ContextWidget):
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
                Input(value="", placeholder="Search Books", id="search-main"),
                Button("Search", id="btn-search"),
                Button("Advanced", id="btn-advanced"),
                id="book-search-section",
                classes="panel-sections book-search",
            ),
            PaginatedTable(
                BookRecord,
                [
                    {
                        "key": "id",
                        "name": "Book Id",
                        "render": lambda id: str(id),
                        "sort_by": "id",
                    },
                    {
                        "key": "title",
                        "name": "Title",
                        "render": lambda title: (
                            title if len(title) <= 50 else title[:47] + "..."
                        )
                        .replace("<i>", "[italic]")
                        .replace("<\\i>", "[/italic]")
                        .replace("\\", ""),
                        "sort_by": "title",
                    },
                    {
                        "key": "length",
                        "name": "Number of Pages",
                        "render": lambda length: str(length),
                        "sort_by": "length",
                    },
                    {
                        "key": "edition",
                        "name": "Edition Name",
                        "render": lambda edition: edition
                        if edition
                        else "Not Specified",
                        "sort_by": "edition",
                    },
                    {
                        "key": "release_dt",
                        "name": "Release Date",
                        "render": lambda release: release.strftime("%b %d, %Y"),
                        "sort_by": "release_dt",
                    },
                    {
                        "key": "isbn",
                        "name": "ISBN",
                        "render": lambda isbn: str(isbn),
                        "sort_by": "isbn",
                    },
                    {
                        "key": "authors",
                        "name": "Authors",
                        "render": lambda authors: ", ".join([a.name for a in authors]),
                        "sort_by": "authors_names_only",
                    },
                    {
                        "key": "editors",
                        "name": "Editors",
                        "render": lambda editors: ", ".join([e.name for e in editors]),
                        "sort_by": "editors_names_only",
                    },
                    {
                        "key": "publishers",
                        "name": "Publishers",
                        "render": lambda publishers: ", ".join(
                            [p.name for p in publishers]
                        ),
                        "sort_by": "publishers_names_only",
                    },
                    {
                        "key": "genres",
                        "name": "Genres",
                        "render": lambda genres: ", ".join(
                            list(set([g.name for g in genres]))
                        ),
                        "sort_by": "genres_names_only",
                    },
                    {
                        "key": "audiences",
                        "name": "Audiences",
                        "render": lambda audiences: ", ".join(
                            list(set([a.name for a in audiences]))
                        ),
                        "sort_by": "audiences_names_only",
                    },
                    {
                        "key": "avg_rating",
                        "name": "Average Rating",
                        "render": lambda rating: str(rating),
                        "sort_by": "avg_rating",
                    },
                ],
                id="book-results-section",
                classes="panel-sections book-results",
                initial_params={"min_length": 100},
                initial_pagination={
                    "limit": 25,
                    "offset": 0,
                    "order": [
                        ["release_dt", "ASC"],
                        ["title", "ASC"],
                    ],
                },
                cursor_type="row"
            ),
            classes="panel books",
            id="app-panel-books",
        )

    def search_update(self, values: Union[SearchFields, None]):
        if values:
            self.query_one("#search-main", expect_type=Input).value = values.get(
                "title", ""
            )
            self.fields = values
            transformed_values = {}
            for k, v in self.fields.items():
                match k:
                    case "released_after":
                        transformed_values[k] = parse(v).isoformat()
                    case "released_before":
                        transformed_values[k] = parse(v).isoformat()
                    case "min_length":
                        transformed_values[k] = int(v)
                    case "max_length":
                        transformed_values[k] = int(v)
                    case "isbn":
                        transformed_values[k] = int(v)
                    case _:
                        transformed_values[k] = v
            self.query_one("#book-results-section", expect_type=PaginatedTable).search(
                transformed_values
            )

    @on(Button.Pressed, "#btn-advanced")
    def on_advanced(self):
        self.app.push_screen(AdvancedSearchModal(self.fields), self.search_update)

    @on(Button.Pressed, "#btn-search")
    def on_search(self):
        self.search_update(self.fields)

    @on(Input.Changed, "#search-main")
    def on_search_change(self, event: Input.Changed):
        if len(event.value) == 0 and "title" in self.fields.keys():
            del self.fields["title"]
        else:
            self.fields["title"] = event.value

    @on(PaginatedTable.CursorEvent)
    def on_row_highlight(self, event: PaginatedTable.CursorEvent):
        self.app.push_screen(BookActionsModal(event.value, id="book-actions-modal"))
