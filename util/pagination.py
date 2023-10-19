from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import DataTable, Button, Digits, Select, Label
from textual.containers import Container, Grid, Middle
from .widget import ContextWidget
from textual.reactive import reactive
from textual import work, on
from textual.coordinate import Coordinate
from .orm import Record, SearchResult, PaginationParams
from typing import Any, Callable, Coroutine, Union
from typing_extensions import TypedDict
from rich.console import RenderableType
from threading import Thread
import math


class PaginatedColumn(TypedDict):
    key: str
    name: str
    render: Callable[[Any], RenderableType]


class PaginatedTable(ContextWidget):
    data: reactive[list[Record]]
    rows: reactive[list[list[Union[str, RenderableType]]]]
    pagination: reactive[PaginationParams]
    result_factory: reactive[type[Record]]
    params: reactive[dict[str, Any]]
    total: reactive[int]
    loading: reactive[bool]
    page_status: reactive[str]
    BINDINGS = [
        ("ctrl+r", "refresh()", "Refresh Data"),
    ]

    def __init__(
        self,
        factory: type[Record],
        columns: list[PaginatedColumn],
        *children: Widget,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
        initial_pagination: PaginationParams = {"offset": 0, "limit": 25, "order": []},
        initial_params: dict[str, Any] = {},
        initial_total: int = 0,
    ) -> None:
        super().__init__(
            *children, name=name, id=id, classes=classes, disabled=disabled
        )
        self.result_factory = factory
        self.data = []
        self.columns = columns
        self.pagination = initial_pagination
        self.params = initial_params
        self.total = initial_total
        self.loading = False
        self.calculate_page_status()

    def calculate_page_status(self) -> None:
        page_size = self.pagination["limit"]
        total_pages = (
            math.ceil(self.total / page_size) if self.total > 0 and page_size > 0 else 1
        )
        current_page = (
            math.floor(
                self.pagination["offset"]
                / (page_size if page_size > 0 else self.pagination["offset"])
            )
            + 1
        )
        self.page_status = f"{current_page} : {total_pages}"
        try:
            self.query_one(".status", expect_type=Digits).update(self.page_status)
        except:
            pass

    def render_row(self, record: Record, row: int) -> None:
        rendered = []
        for c in self.columns:
            if hasattr(record, c["key"]):
                rendered.append(c["render"](getattr(record, c["key"])))
            else:
                rendered.append("Undefined")

        self.rows[row] = rendered

        for column in range(len(self.rows[row])):
            self.query_one(".paginated-table", expect_type=DataTable).update_cell_at(
                Coordinate(row, column), self.rows[row][column], update_width=True
            )

    def render_rows(self):
        self.rows = [["" for column in self.columns] for record in self.data]
        table = self.query_one(".paginated-table", expect_type=DataTable)
        table.clear()
        table.add_rows(self.rows)
        for row in range(len(self.data)):
            Thread(target=self.render_row, args=[self.data[row], row]).start()

    @work(exclusive=True, thread=True, group="pagination-update")
    def update_data(self):
        """Update data from current attrs"""
        self.loading = True
        result = self.result_factory.search(
            self.context.orm, self.pagination, **self.params
        )
        self.total = result.total
        self.data = result.results
        self.render_rows()
        self.loading = False
        self.calculate_page_status()

    def action_refresh(self):
        self.update_data()

    def compose(self) -> ComposeResult:
        yield Container(
            DataTable(classes="paginated-table"),
            Grid(
                Button("<- Previous", classes="pagination-control-item previous"),
                Middle(Label(""), classes="pagination-control-item spacer"),
                Digits(self.page_status, classes="pagination-control-item status"),
                Middle(Label(""), classes="pagination-control-item spacer"),
                Button("Next ->", classes="pagination-control-item next"),
                Select(
                    [("10", 10), ("25", 25), ("50", 50)],
                    classes="pagination-control-item page-size",
                    value=25,
                    allow_blank=False,
                ),
                classes="pagination-controls",
            ),
            id=self.id,
            classes=" ".join(self.classes) + " pagination-root",
        )

    def on_mount(self) -> None:
        table = self.query_one(".paginated-table", expect_type=DataTable)
        table.add_columns(*[c["name"] for c in self.columns])
        self.update_data()

    @on(Button.Pressed, ".pagination-control-item.previous")
    def on_previous_pressed(self):
        pass

    @on(Button.Pressed, ".pagination-control-item.next")
    def on_next_pressed(self):
        pass
