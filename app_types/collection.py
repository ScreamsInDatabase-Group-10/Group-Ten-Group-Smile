from psycopg import Connection
from app_types.book import BookRecord
from app_types.user import UserRecord
from util import orm
from util.orm import (
    Record,
    ORM,
    SearchResult,
    SearchCondition,
    PaginationParams,
    search_internal,
)
from typing import Literal, Optional, Union


class CollectionRecord(Record):
    def __init__(
            self,
            db: Connection,
            table: str,
            orm: ORM,
            id: int,
            name: str,
            _books: list[BookRecord] = None,
            _book_count: int = None,
            _user: UserRecord = None
    ) -> None:
        self.db = db
        self.table = table
        self.id = id
        self.name = name
        self.cache = {
            "books": _books,
            "book_count": _book_count,
            "user": _user
        }

    def save(self) -> None:
        # TODO: more fields
        self.db.execute(
            "UPDATE "
            + self.table
            + "SET NAME = %s WHERE ID = %s"(
                self.name,
                self.id
            )
        )

    def delete(self) -> None:
        self.db.execute("DELETE FROM " + self.table +
                        " WHERE id = %s", (self.id,))
        self.db.commit()

    # TODO
    @property
    def book_count(self) -> int:
        if self.cache["book_count"] != None:
            return self.cache["book_count"]
        raise NotImplementedError

    @property
    def books(self) -> list[BookRecord]:
        if self.cache["books"] != None:
            return self.cache["books"]
        cursor = self.db.execute(
            "SELECT * FROM books AS root WHERE id IN (SELECT book_id FROM books_collections WHERE collection_id = %(id)s)",
            {"id": self.id},
        )
        results = [
            BookRecord(self.db, "audiences", self.orm, *r)
            for r in cursor.fetchall()
        ]
        cursor.close()

        self.cache["books"] = results
        return results

    @property
    def user(self) -> UserRecord:
        if self.cache["user"] != None:
            return self.cache["user"]
        cursor = self.db.execute(
            "SELECT user_id FROM users_collections WHERE collection_id = %(id)s",
            {"id": self.id}
        )
        result = UserRecord(self.db, "users", self.orm, *(cursor.fetchone()))
        cursor.close()

        self.cache["user"] = result
        return result

    @classmethod
    def create(cls, name: str, ) -> Union["CollectionRecord", None]:
        # TODO: next_id is not safe. Maybe improve?
        next_id = orm.next_available_id("collections")
        raise NotImplementedError
