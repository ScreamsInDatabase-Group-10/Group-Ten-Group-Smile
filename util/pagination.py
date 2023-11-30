from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import DataTable, Button, Static, Select
from textual.containers import Container, Grid
from .widget import ContextWidget
from textual.reactive import reactive
from textual import work, on
from textual.coordinate import Coordinate
from textual.message import Message
from .orm import Record, SearchResult, PaginationParams
from typing import Any, Callable, Union, Optional
from typing_extensions import TypedDict
from rich.console import RenderableType
from threading import Thread
import math


class PaginatedColumn(TypedDict):
    key: str
    name: str
    render: Callable[[Any], RenderableType]
    sort_by: Optional[str]


class PaginatedTable(ContextWidget):
    data: reactive[list[Record]]
    rows: reactive[list[list[Union[str, RenderableType]]]]
    pagination: reactive[PaginationParams]
    result_factory: reactive[type[Record]]
    params: reactive[dict[str, Any]]
    total: reactive[int]
    page_status: reactive[str]
    cursor_mode: reactive[str]
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
        cursor_type: str = "none",
    ) -> None:
        """Paginated Table Class

        Args:
            factory (type[Record]): Record subclass to initialize
            columns (list[PaginatedColumn]): List of PaginatedColumn instances
            name (str | None, optional): Element name. Defaults to None.
            id (str | None, optional): Element ID. Defaults to None.
            classes (str | None, optional): Element class string. Defaults to None.
            disabled (bool, optional): Element disabled. Defaults to False.
            initial_pagination (_type_, optional): Initial pagination setup. Defaults to {"offset": 0, "limit": 25, "order": []}.
            initial_params (dict[str, Any], optional): Initial search params. Defaults to {}.
            initial_total (int, optional): Initial total results. Defaults to 0.
        """
        super().__init__(
            *children, name=name, id=id, classes=classes, disabled=disabled
        )
        self.result_factory = factory
        self.data = []
        self.columns = columns
        self.default_pagination = initial_pagination
        self.pagination = initial_pagination
        self.params = initial_params
        self.total = initial_total
        self.calculate_page_status()
        self.lock = False
        self.cursor_mode = cursor_type
        self.cursor_waiting = True

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
        self.page_status = f"[bold]{current_page} / {total_pages}[/bold]"
        try:
            self.query_one(".status", expect_type=Static).update(self.page_status)
        except:
            pass

    def render_row(self, record: Record, row: int, table: DataTable) -> None:
        rendered = []
        for c in self.columns:
            if hasattr(record, c["key"]):
                rendered.append(c["render"](getattr(record, c["key"])))
            else:
                rendered.append("Undefined")

        self.rows[row] = rendered

        table.add_row(*rendered)

    def render_rows(self):
        self.rows = [["" for column in self.columns] for record in self.data]
        table = self.query_one(".paginated-table", expect_type=DataTable)
        table.clear()
        for row in range(len(self.data)):
            self.render_row(self.data[row], row, table)

    @work(exclusive=True, thread=True, group="pagination-update")
    def update_data(self):
        """Update data from current attrs"""
        while self.lock:
            pass
        self.cursor_waiting = True
        self.lock = True
        table = self.query_one(".paginated-table", expect_type=DataTable)
        table.clear(columns=True)
        result = self.result_factory.search(
            self.context.orm, self.pagination, **self.params
        )
        self.total = result.total
        self.data = result.results
        table.add_columns(*self.get_column_sorts())
        self.render_rows()
        self.calculate_page_status()
        self.query_one(".paginated-table", expect_type=DataTable).refresh()
        self.lock = False

    def action_refresh(self):
        self.update_data()

    def compose(self) -> ComposeResult:
        yield Container(
            DataTable(
                classes="paginated-table",
                show_cursor=True,
                cursor_type=self.cursor_mode,
            ),
            Grid(
                Button("<- Previous", classes="pagination-control-item previous"),
                Static(self.page_status, classes="pagination-control-item status"),
                Button("Next ->", classes="pagination-control-item next"),
                Select(
                    [("10", 10), ("25", 25), ("50", 50)],
                    classes="pagination-control-item page-size",
                    value=25,
                    allow_blank=False,
                ),
                classes="pagination-controls",
            ),
            classes=" ".join(self.classes) + " pagination-root",
        )

    def on_mount(self) -> None:
        table = self.query_one(".paginated-table", expect_type=DataTable)
        table.add_columns(*[c["name"] for c in self.columns])
        self.update_data()

    @on(Button.Pressed, ".pagination-control-item.previous")
    def on_previous_pressed(self):
        self.go_previous()

    @on(Button.Pressed, ".pagination-control-item.next")
    def on_next_pressed(self):
        self.go_next()

    @on(Select.Changed, ".pagination-control-item.page-size")
    def on_page_size_changed(self, event: Select.Changed):
        self.pagination["limit"] = event.value
        self.update_data()

    def go_previous(self):
        if self.pagination["offset"] > 0:
            self.pagination["offset"] = max(
                0, self.pagination["offset"] - self.pagination["limit"]
            )
            self.update_data()

    def go_next(self):
        if self.pagination["offset"] < self.total - self.pagination["limit"]:
            self.pagination["offset"] = min(
                self.total - self.pagination["limit"],
                self.pagination["offset"] + self.pagination["limit"],
            )
            self.update_data()

    @on(DataTable.HeaderSelected)
    def on_column_select(self, event: DataTable.HeaderSelected):
        if "sort_by" in self.columns[event.column_index].keys():
            if self.columns[event.column_index]["sort_by"] in [
                sort[0] for sort in self.pagination["order"]
            ]:
                cur_index = self.pagination["order"].index(
                    next(
                        filter(
                            lambda x: x[0]
                            == self.columns[event.column_index]["sort_by"],
                            self.pagination["order"],
                        )
                    )
                )
                if self.pagination["order"][cur_index][1] == "ASC":
                    new = self.pagination["order"][cur_index]
                    new[1] = "DESC"
                    del self.pagination["order"][cur_index]
                    self.pagination["order"].insert(0, new)
                else:
                    del self.pagination["order"][cur_index]
            else:
                self.pagination["order"].insert(
                    0, [self.columns[event.column_index]["sort_by"], "ASC"]
                )
            self.update_data()

    def get_column_sorts(self) -> list[str]:
        new_columns = []
        for c in range(len(self.columns)):
            if (
                "sort_by" in self.columns[c].keys()
                and self.columns[c]["sort_by"] != None
            ):
                if [self.columns[c]["sort_by"], "ASC"] in self.pagination["order"]:
                    new_columns.append("▲ " + self.columns[c]["name"])
                elif [self.columns[c]["sort_by"], "DESC"] in self.pagination["order"]:
                    new_columns.append("▼ " + self.columns[c]["name"])
                else:
                    new_columns.append("◆ " + self.columns[c]["name"])
            else:
                new_columns.append(self.columns[c]["name"])
        return new_columns

    def search(self, params: dict[str, Any]):
        """Update search params

        Args:
            params (dict[str, Any]): New search parameters
        """
        self.pagination = self.default_pagination.copy()
        self.params = params
        self.update_data()

    def watch_cursor_mode(self, old, new):
        self.cursor_waiting = True
        self.query_one(".paginated-table", expect_type=DataTable).cursor_type = new

    class CursorEvent(Message):
        def __init__(self, value: Any) -> None:
            super().__init__()
            self.value = value

    @on(DataTable.CellHighlighted)
    def on_cursor_event_cell(self, event: DataTable.CellHighlighted):
        if self.cursor_waiting:
            self.cursor_waiting = False
            return
        self.post_message(self.CursorEvent(event.value))

    @on(DataTable.RowHighlighted)
    def on_cursor_event_row(self, event: DataTable.RowHighlighted):
        if self.cursor_waiting:
            self.cursor_waiting = False
            return
        self.post_message(self.CursorEvent(self.data[event.cursor_row]))

    @on(DataTable.ColumnHighlighted)
    def on_cursor_event_column(self, event: DataTable.ColumnHighlighted):
        if self.cursor_waiting:
            self.cursor_waiting = False
            return
        column = self.columns[event.cursor_column]
        key = column["key"]
        return self.post_message(self.CursorEvent([getattr(d, key) for d in self.data]))
