from textual.app import ComposeResult
from textual.widgets import Placeholder, Input, Button
from textual.containers import Container, Horizontal
from util import ContextWidget, PaginatedTable, ContextModal
from app_types import BookRecord
from datetime import datetime
from typing_extensions import TypedDict


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


class AdvancedSearchModal(ContextModal):
    def __init__(
        self,
        field_values: SearchFields,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name, id, classes)
        self.fields = field_values

    def compose(self) -> ComposeResult:
        return super().compose()


class BooksPanel(ContextWidget):
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
            ),
            classes="panel books",
            id="app-panel-books",
        )
