from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Button, DataTable
from util import ContextWidget
from textual.containers import Container, Horizontal
from textual import on, work
from textual.reactive import reactive
from typing import Literal
from app_types import BookRecord
from datetime import datetime


class RecommendationPanel(ContextWidget):
    mode: reactive[
        Literal["last-90", "followers-read", "this-month", "for-you"]
    ] = reactive("last-90")
    data: reactive[list[BookRecord]] = reactive(lambda: list())

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

    @work(name="data.last-90", thread=True)
    def get_data_last_90(self):
        data = self.context.db.execute(
            "SELECT * FROM view_rec_90 ORDER BY count DESC LIMIT 20"
        )
        self.data = [
            BookRecord._from_search(self.context.db, "books", self.context.orm, *i)
            for i in data
        ]

    @work(name="data.this-month", thread=True)
    def get_data_this_month(self):
        data = self.context.db.execute(
            "SELECT * FROM view_rec_this_month ORDER BY avg_rating DESC LIMIT 5"
        )
        self.data = [
            BookRecord._from_search(self.context.db, "books", self.context.orm, *i)
            for i in data
        ]

    @work(name="data.for-you", thread=True)
    def get_data_for_you(self):
        data = self.context.db.execute(
            """
                SELECT * FROM view_books 
                WHERE avg_rating IS NOT NULL AND id IN (
                    SELECT book_id FROM books_genres
                    WHERE genre_id IN (
                        SELECT DISTINCT genre_id FROM books_genres
                        WHERE book_id IN (
                            SELECT book_id FROM users_ratings
                            WHERE user_id = %s ORDER BY rating DESC LIMIT 100
                        )
                    )
                )
                ORDER BY avg_rating DESC
                LIMIT 20
            """,
            [self.context.logged_in.id],
        )
        self.data = [
            BookRecord._from_search(self.context.db, "books", self.context.orm, *i)
            for i in data
        ]

    @work(name="data.followers-read", thread=True)
    def get_data_followers_read(self):
        data = self.context.db.execute(
            """
            SELECT * FROM view_books WHERE avg_rating IS NOT NULL AND id in (SELECT books_collections.book_id FROM books_collections 
                WHERE books_collections.collection_id IN (
                    SELECT users_collections.collection_id FROM users_collections
                    WHERE users_collections.user_id IN (
                        SELECT users_following.user_id FROM users_following 
                        WHERE users_following.following_id = %s
                    )
                ) 
                GROUP BY books_collections.book_id)
            ORDER BY avg_rating DESC
            LIMIT 20
        """,
            [self.context.logged_in.id],
        )
        self.data = [
            BookRecord._from_search(self.context.db, "books", self.context.orm, *i)
            for i in data
        ]

    def compose(self) -> ComposeResult:
        yield Container(
            Horizontal(
                Button(
                    label="Last 90 Days",
                    classes="rec-control last-90 active",
                    name="last-90",
                ),
                Button(
                    label="Read By Followers",
                    classes="rec-control followers-read",
                    name="followers-read",
                ),
                Button(
                    label="This Month",
                    classes="rec-control this-month",
                    name="this-month",
                ),
                Button(label="For You", classes="rec-control for-you", name="for-you"),
            ),
            DataTable(id="data-display"),
            classes="panel rec",
            id="app-panel-rec",
        )

    def watch_data(self, old: list[BookRecord], new: list[BookRecord]):
        table = self.query_one("#data-display", expect_type=DataTable)
        if len(new) > 0:
            rows = [
                [
                    str(rec.id),
                    rec.title,
                    rec.length,
                    rec.edition if rec.edition else "",
                    rec.release_dt.strftime("%b %d, %Y"),
                    str(rec.isbn),
                    ", ".join([a.name for a in rec.authors]),
                    ", ".join([e.name for e in rec.editors]),
                    ", ".join([p.name for p in rec.publishers]),
                    ", ".join([g.name for g in rec.genres]),
                    ", ".join([a.name for a in rec.audiences]),
                    str(rec.avg_rating),
                ]
                for rec in new
            ]
            table.clear()
            table.add_rows(rows)
        else:
            table.clear()
            table.add_rows([["" for i in range(12)]])

    def on_mount(self):
        table = self.query_one("#data-display", expect_type=DataTable)
        table.add_columns(
            "Id",
            "title",
            "Number of Pages",
            "Edition Name",
            "Release Date",
            "ISBN",
            "Authors",
            "Editors",
            "Publishers",
            "Genres",
            "Audiences",
            "Average Rating",
        )
        self.get_data_last_90()

    @on(Button.Pressed, selector=".rec-control")
    def handle_tab_click(self, event: Button.Pressed):
        self.mode = event.button.name
        for k in self.query(".rec-control.active"):
            k.remove_class("active")
        self.query_one(f".rec-control.{self.mode}", expect_type=Button).add_class(
            "active"
        )

        match self.mode:
            case "last-90":
                self.get_data_last_90()
            case "this-month":
                self.get_data_this_month()
            case "followers-read":
                self.get_data_followers_read()
            case "for-you":
                self.get_data_for_you()
