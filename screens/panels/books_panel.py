from textual.app import ComposeResult
from textual.widgets import Placeholder
from textual.containers import Container
from util import ContextWidget, PaginatedTable
from app_types import BookRecord
from datetime import datetime


class BooksPanel(ContextWidget):
    def compose(self) -> ComposeResult:
        yield Container(
            Placeholder(
                "Search Bar",
                id="book-search-section",
                classes="panel-sections book-search",
            ),
            PaginatedTable(
                BookRecord,
                [
                    {"key": "id", "name": "Book Id", "render": lambda id: str(id)},
                    {
                        "key": "title",
                        "name": "Title",
                        "render": lambda title: (
                            title if len(title) <= 50 else title[:47] + "..."
                        )
                        .replace("<i>", "[italic]")
                        .replace("<\\i>", "[/italic]")
                        .replace("\\", ""),
                    },
                    {
                        "key": "length",
                        "name": "Number of Pages",
                        "render": lambda length: str(length),
                    },
                    {
                        "key": "edition",
                        "name": "Edition Name",
                        "render": lambda edition: edition
                        if edition
                        else "Not Specified",
                    },
                    {
                        "key": "release_dt",
                        "name": "Release Date",
                        "render": lambda release: release.strftime("%b %d, %Y"),
                    },
                    {"key": "isbn", "name": "ISBN", "render": lambda isbn: str(isbn)},
                    {
                        "key": "authors",
                        "name": "Authors",
                        "render": lambda authors: ", ".join([a.name for a in authors]),
                    },
                    {
                        "key": "publishers",
                        "name": "Publishers",
                        "render": lambda publishers: ", ".join(
                            [p.name for p in publishers]
                        ),
                    },
                ],
                id="book-results-section",
                classes="panel-sections book-results",
                initial_params={"min_length": 100},
            ),
            classes="panel books",
            id="app-panel-books",
        )
