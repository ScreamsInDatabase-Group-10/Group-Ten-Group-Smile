from psycopg import Connection, Cursor
from typing import Literal, Optional, Any, Union
from dataclasses import dataclass, asdict
from .exceptions import *
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
    results: list["Record"]
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
    orm: "ORM",
    table: str,
    factory: type["Record"],
    conditions: Optional[list[SearchCondition]] = None,
    order: Optional[ORDER_PARAM] = None,
    offset: Optional[int] = None,
    limit: Optional[int] = None,
    format_query: str = "SELECT * FROM {table} AS root{conditions}{order}{offset}{limit}"
) -> SearchResult:
    """Does the actual searching part (querying, result count, etc)

    Args:
        orm (ORM): ORM Object
        table (str): Table to search
        factory (type[Record]): Class factory
        conditions (Optional[list[SearchCondition]], optional): List of conditions and format values. Defaults to None.
        order (Optional[ORDER_PARAM], optional): Ordering data. Defaults to None.
        offset (Optional[int], optional): First record to get. Defaults to None.
        limit (Optional[int], optional): Max number of records past offset to get. Defaults to None.

    Returns:
        SearchResult: Search result
    """
    fields = []
    assembled = format_query.format(
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

    assembled_count = "SELECT COUNT(*) FROM {table} AS root{conditions}".format(
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
        total_count,
    )

TABLE_NAMES = Literal[
    "books",
    "contributors",
    "genres",
    "audiences",
    "users",
    "collections",
]

table_mapping: dict[TABLE_NAMES, str] = {
    "books": "books",
    "contributors": "contributors",
    "genres": "genres",
    "audiences": "audiences",
    "users": "users",
    "collections": "collections",
}

# Record class
class Record:
    def __init__(self, db: Connection, table: str, orm: "ORM", *args) -> None:
        """Initializer

        Args:
            db (Connection): DB Connection, handled by ORM
            table (str): Table name
            orm (ORM): ORM object
        """
        self.db = db
        self.table = table
        self.orm = orm

    # Implement in subclasses to save to database automatically
    def save(self):
        raise NotImplementedError

    # Implement in subclass to delete from database automatically
    def delete(self):
        raise NotImplementedError
    
    def __repr__(self) -> str:
        return "Record<{}>".format(", ".join([f"{k} = {v}" for k, v in self.__dict__.items() if not k in ["db", "table", "orm"]]))
    
    def dict(self) -> dict:
        return {k:v for k, v in self.__dict__.items() if not k in ["db", "table", "orm"]}
    
    @classmethod
    def search(self, orm: "ORM", pagination: PaginationParams, **kwargs) -> SearchResult:
        raise NotImplementedError

# Extremely basic ORM, just abstracts away some common tasks into OOP
class ORM:
    def __init__(self, connection: Connection) -> None:
        """Create ORM

        Args:
            connection (Connection): Database connection object
        """
        self.db = connection
        self.factories: dict[TABLE_NAMES, type[Record]] = {}

    def register(self, table: TABLE_NAMES, record_factory: type[Record]):
        """Register Record type to table

        Args:
            table (TABLE_NAMES): Table key
            record_factory (type[Record]): Record subclass
        """
        self.factories[table] = record_factory

    def get_record_by_id(self, table: TABLE_NAMES, id: int) -> Optional[Record]:
        """Gets a single record by its ID

        Args:
            table (TABLE_NAMES): Table key
            id (int): Record ID

        Raises:
            ORMRegistryError: Raised if the table record type is not registered

        Returns:
            Optional[Record]: Returns the Record object or None
        """
        if not table in self.factories.keys():
            raise ORMRegistryError(table)

        result_cursor = self.db.execute(
            "SELECT * FROM " + table + " WHERE id = %(id)s;", {"id": id}
        )
        result = result_cursor.fetchone()
        result_cursor.close()
        if result:
            return self.factories[table](self.db, table_mapping[table], self, *result)
        else:
            return None

    def get_records_by_condition(
        self, table: TABLE_NAMES, condition: str, limit: int = None
    ) -> list[Record]:
        """Get results by a condition (Text after a WHERE statement)

        Args:
            table (TABLE_NAMES): Table key
            condition (str): Condition string (SELECT * FROM table WHERE {condition})
            limit (int, optional): Max number of results to return. Defaults to None.

        Raises:
            ORMRegistryError: Raised if the table record type is not registered

        Returns:
            list[Record]: List of generated Record objects
        """
        if not table in self.factories.keys():
            raise ORMRegistryError(table)

        result_cursor = self.db.execute(
            "SELECT * FROM " + table + " WHERE %(condition)s;", {"condition": condition}
        )
        if limit:
            result = [
                self.factories[table](self.db, table_mapping[table], self, *i)
                for i in result_cursor.fetchmany(size=limit)
            ]
        else:
            result = [
                self.factories[table](self.db, table_mapping[table], self, *i)
                for i in result_cursor.fetchall()
            ]

        result_cursor.close()
        return result

    def get_records_by_query_suffix(
        self, table: TABLE_NAMES, query_suffix: str, params={}
    ) -> list[Record]:
        """Get results through a query

        Args:
            table (TABLE_NAMES): Table key
            query_suffix (str): Query suffix (ie SELECT * FROM table {suffix})
            params (dict, optional): Parameters for a parameterized string. Defaults to {}.

        Raises:
            ORMRegistryError: Raised if the table record type is not registered

        Returns:
            list[Record]: List of generated Record objects
        """
        if not table in self.factories.keys():
            raise ORMRegistryError(table)

        result_cursor = self.db.execute(
            f"SELECT * FROM {table} " + query_suffix, params
        )
        results = [
            self.factories[table](self.db, table_mapping[table], self, *i)
            for i in result_cursor.fetchall()
        ]
        result_cursor.close()
        return results
    
    def get_records_from_cursor(self, table: TABLE_NAMES, cursor: Cursor) -> list[Record]:
        """Gets an array of records from a cursor (potentially unsafe)

        Args:
            table (TABLE_NAMES): Table name
            cursor (Cursor): Raw psycopg3 cursor

        Returns:
            list[Record]: List of returned records
        """
        return [
            self.factories[table](self.db, table_mapping[table], self, *i)
            for i in cursor.fetchall()
        ]

    def next_available_id(self, table: TABLE_NAMES) -> int:
        """Returns the next available ID in the table. 
                This is not assumed to be safe for more than 1 client, 
                we just aren't using serial IDs so this was a quick hack around it

        Args:
            table (TABLE_NAMES): Table name

        Returns:
            int: Next available ID.
        """
        return self.db.execute("SELECT MAX(id) FROM " + table).fetchone()[0] + 1
