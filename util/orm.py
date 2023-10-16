from psycopg import Connection, Cursor
from typing import Literal, Optional
from .exceptions import *

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
