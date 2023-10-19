from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import DataTable
from .widget import ContextWidget
from textual.reactive import reactive
from textual import events, work
from textual.coordinate import Coordinate
from .orm import Record, SearchResult, PaginationParams
from typing import Any, Callable, Coroutine, Union
from typing_extensions import TypedDict
from rich.console import RenderableType
from threading import Thread

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
        initial_pagination: PaginationParams = {"offset": 0, "limit": 50, "order": []},
        initial_params: dict[str, Any] = {},
        initial_total: int = 0
    ) -> None:
        super().__init__(
            *children, name=name, id=id, classes=" ".join([*(classes.split(" ") if classes else []), "paginated-table"]), disabled=disabled
        )
        self.result_factory = factory
        self.data = []
        self.columns = columns
        self.pagination = initial_pagination
        self.params = initial_params
        self.total = initial_total
        self.loading = False

    def render_row(self, record: Record, row: int) -> None:
        rendered = []
        for c in self.columns:
            if hasattr(record, c["key"]):
                rendered.append(c["render"](getattr(record, c["key"])))
            else:
                rendered.append("Undefined")

        self.rows[row] = rendered

        for column in range(len(self.rows[row])):
            self.query_one(".paginated-table", expect_type=DataTable).update_cell_at(Coordinate(row, column), self.rows[row][column], update_width=True)

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
        result = self.result_factory.search(self.context.orm, self.pagination, **self.params)
        self.total = result.total
        self.data = result.results
        self.render_rows()
        self.loading = False

    def action_refresh(self):
        self.update_data()

    def compose(self) -> ComposeResult:
        yield DataTable(id=self.id, classes=" ".join(self.classes))

    def on_mount(self) -> None:
        table = self.query_one(".paginated-table", expect_type=DataTable)
        table.add_columns(*[c["name"] for c in self.columns])
        self.update_data()
