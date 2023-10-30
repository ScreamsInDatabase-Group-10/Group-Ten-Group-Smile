from psycopg import Connection
from util.orm import Record, ORM
from datetime import datetime
import time
from typing import Union
#from app_types.collection import CollectionRecord
from app_types.book import BookRecord


class UserRecord(Record):
    def __init__(
        self,
        db: Connection,
        table: str,
        orm: ORM,
        id: int,
        creation_dt: datetime,
        access_dt: datetime,
        name_first: str,
        name_last: str,
        email: str,
        password: str,
        *args
    ) -> None:
        super().__init__(db, table, orm)
        self.id = id
        self.creation_dt = creation_dt
        self.access_dt = access_dt
        self.name_first = name_first
        self.name_last = name_last
        self.email = email
        self.password = password
        #self.cache = {
        #    "collections": None
        #}
    
    def save(self):
        self.db.execute(
            "UPDATE "
            + self.table
            + " SET creation_dt = %s, access_dt = %s, name_first = %s, name_last = %s, email = %s, password = %s WHERE id = %s",
            (
                self.creation_dt,
                self.access_dt,
                self.name_first,
                self.name_last,
                self.email,
                self.password,
                self.id
            ),
        )
        self.db.commit()

    def delete(self):
        self.db.execute("DELETE FROM " + self.table + " WHERE id = %s", (self.id,))
        self.db.commit()

    def collections(self) -> list("CollectionRecord"):
        cursor = self.db.execute(
            f"SELECT * from collections WHERE id IN (SELECT collection_id from users_collections where user_id = {self.id})"
        )
        results = [CollectionRecord(self.db, "collections", self.orm, *r) for r in cursor.fetchall()]
        cursor.close()

        #self.cache["collections"] = results
        return results

    
    # Create a user, handle ID generation and times automatically
    @classmethod
    def create(cls, orm: ORM, name_first: str, name_last: str, email: str, password: str) -> Union["UserRecord", None]:
        next_id = orm.next_available_id("users")
        creation = datetime.fromtimestamp(time.time())
        access = datetime.fromtimestamp(time.time())

        try:
            orm.db.execute("INSERT INTO users (id, creation_dt, access_dt, name_first, name_last, email, password) VALUES (%s, %s, %s, %s, %s, %s, %s)", (
                next_id,
                creation,
                access,
                name_first,
                name_last,
                email,
                password
            ))
            orm.db.commit()
            return UserRecord(orm.db, "users", orm, next_id, creation, access, name_first, name_last, email, password)
        except:
            return None

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
            + "SET NAME = %s WHERE ID = %s",
            (
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
        next_id = ORM.next_available_id("collections")
        raise NotImplementedError