from .orm import Record, ORM
from dataclasses import dataclass
from typing import Any, Literal, Optional
from typing_extensions import TypedDict

ORDER_PARAM = list[list[str, Literal["ASC", "DESC"]]]


@dataclass
class SearchQuery:
    parameters: dict[str, Any]
    order_by: ORDER_PARAM
    offset: int
    limit: int


@dataclass
class SearchResult:
    results: list[Record]
    offset: int
    limit: int
    total: int


@dataclass
class SearchCondition:
    condition: str
    fields: list[Any]


class PaginationParams(TypedDict):
    offset: Optional[int]
    limit: Optional[int]
    order: Optional[ORDER_PARAM]


def search_internal(
    orm: ORM,
    table: str,
    factory: type[Record],
    conditions: Optional[list[SearchCondition]] = None,
    order: Optional[ORDER_PARAM] = None,
    offset: Optional[int] = None,
    limit: Optional[int] = None,
) -> SearchResult:
    fields = []
    assembled = "SELECT * FROM {table}{conditions}{order}{offset}{limit}".format(
        table=table,
        conditions=" WHERE " + " AND ".join([c.condition for c in conditions])
        if len(conditions) > 0
        else "",
        order=" ORDER BY " + ", ".join([o[0] + " " + o[1] for o in order])
        if order
        else "",
        offset=" OFFSET " + str(offset) if offset != None else "",
        limit=" LIMIT " + str(limit) if limit != None else "",
    )

    assembled_count = "SELECT COUNT(*) FROM {table}{conditions}".format(
        table=table,
        conditions=" WHERE " + " AND ".join([c.condition for c in conditions])
        if len(conditions) > 0
        else "",
    )

    for c in conditions:
        fields.extend(c.fields)

    cursor = orm.db.execute(assembled, fields)
    cursor_count = orm.db.execute(assembled_count, fields)
    total_count = cursor_count.fetchone()[0]
    results = [factory(orm.db, table, orm, *r) for r in cursor.fetchall()]
    cursor.close()
    cursor_count.close()
    return SearchResult(
        results,
        offset if offset != None else 0,
        limit if limit != None else total_count,
        total_count,
    )
