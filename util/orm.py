from psycopg import Connection
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
    "contributors" : "contributors",
    "genres": "genres",
    "audiences": "audiences",
    "users": "users",
    "collections": "collections"
}

class Record:
    def __init__(self, db: Connection, *args) -> None:
        self.db = db

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
        
        result_cursor = self.db.execute("SELECT * FROM %(table)s WHERE id = %(id)s;", {"table": table, "id": id})
        result = result_cursor.fetchone()
        result_cursor.close()
        if result:
            return self.factories[table](self.db, *result)
        else:
            return None
        
    def get_records_by_condition(self, table: TABLE_NAMES, condition: str, limit: int = None) -> list[Record]:
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
        
        result_cursor = self.db.execute("SELECT * FROM %(table)s WHERE %(condition)s;", {"table": table, "condition": condition})
        if limit:
            result = [self.factories[table](self.db, *i) for i in result_cursor.fetchmany(size=limit)]
        else:
            result = [self.factories[table](self.db, *i) for i in result_cursor.fetchall()]
        
        result_cursor.close()
        return result
    
    def get_records_by_query_suffix(self, table: TABLE_NAMES, query_suffix: str, params = {}) -> list[Record]:
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
        
        result_cursor = self.db.execute("SELECT * FROM %(table)s " + query_suffix, dict(table=table, **params))
        results = [self.factories[table](self.db, *i) for i in result_cursor.fetchall()]
        result_cursor.close()
        return results
