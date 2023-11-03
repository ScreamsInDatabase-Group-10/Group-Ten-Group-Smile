from psycopg import Connection
from util.orm import (
    PaginationParams,
    Record,
    ORM,
    SearchCondition,
    SearchResult,
    search_internal,
)
from datetime import datetime
import time
from typing import Optional, Union
from app_types.book import BookRecord
USER_FMT = """
SELECT
        users.id as id,
        users.name_first as name_first,
        users.name_last as name_last,
        users.email as email,
        users.creation_dt as creation_dt,
        users.access_dt as access_dt,
        users.password as password
    FROM {table}
    {conditions}
    {order}
    {offset}
    {limit}
"""

USER_FMT_COUNT = """
SELECT
        COUNT(users.id)
    from {table}
    {conditions}
"""


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
                self.id,
            ),
        )
        self.db.commit()

    def delete(self):
        self.db.execute("DELETE FROM " + self.table + " WHERE id = %s", (self.id,))
        self.db.commit()

    def collections(self) -> list("CollectionRecord"):
        cursor = self.db.execute(
            f"SELECT * from collections WHERE id IN (SELECT collection_id from users_collections where user_id = {self.id}) ORDER BY name"
        )
        results = [CollectionRecord(self.db, "collections", self.orm, *r) for r in cursor.fetchall()]
        cursor.close()

        #self.cache["collections"] = results
        return results

    
    # Create a user, handle ID generation and times automatically
    @classmethod
    def create(
        cls, orm: ORM, name_first: str, name_last: str, email: str, password: str
    ) -> Union["UserRecord", None]:
        next_id = orm.next_available_id("users")
        creation = datetime.fromtimestamp(time.time())
        access = datetime.fromtimestamp(time.time())

        try:
            orm.db.execute(
                "INSERT INTO users (id, creation_dt, access_dt, name_first, name_last, email, password) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (next_id, creation, access, name_first, name_last, email, password),
            )
            orm.db.commit()
            return UserRecord(
                orm.db,
                "users",
                orm,
                next_id,
                creation,
                access,
                name_first,
                name_last,
                email,
                password,
            )
        except:
            return None

    @classmethod
    def _from_search(
        cls,
        db: Connection,
        table: str,
        orm: ORM,
        id: int,
        name_first: str,
        name_last: str,
        email: str,
        creation_dt: datetime,
        access_dt: datetime,
        password: str,
    ):
        return UserRecord(
            db,
            table,
            orm,
            id,
            creation_dt,
            access_dt,
            name_first,
            name_last,
            email,
            password,
        )

    @classmethod
    def search(
        self,
        orm: ORM,
        pagination: PaginationParams,
        id: Optional[str] = None,
        name_first: Optional[str] = None,
        name_last: Optional[str] = None,
        email: Optional[str] = None,
    ) -> SearchResult:
        fields = []

        if id != None:
            fields.append(SearchCondition("id = %s", [id]))
        if name_first != None:
            fields.append(
                SearchCondition("name_first ilike %s", ["%%" + name_first + "%%"])
            )
        if name_last != None:
            fields.append(
                SearchCondition("name_last ilike %s", ["%%" + name_last + "%%"])
            )
        if email != None:
            fields.append(SearchCondition("email ilike %s", ["%%" + email + "%%"]))

        results = search_internal(
            orm,
            "users",
            UserRecord._from_search,
            fields,
            pagination.get("order") if pagination else None,
            pagination.get("offset") if pagination else None,
            pagination.get("limit") if pagination else None,
            format_query=USER_FMT,
            # format_count_query=USER_FMT_COUNT,
        )

        return results
    
    @property
    def followers(self) -> list["UserRecord"]:
        return self.orm.get_records_from_cursor("users", self.db.execute("SELECT * FROM users WHERE id IN (SELECT user_id FROM users_following WHERE following_id = %s)", [self.id]))

    @property
    def following(self) -> list["UserRecord"]:
        return self.orm.get_records_from_cursor("users", self.db.execute("SELECT * FROM users WHERE id IN (SELECT following_id FROM users_following WHERE user_id = %s)", [self.id]))

class CollectionRecord(Record):
    def __init__(
            self,
            db: Connection,
            table: str,
            orm: ORM,
            id: int,
            name: str,
            _book_count: int = None,
            _user: UserRecord = None
    ) -> None:
        self.orm = orm # TODO: put this in the super class
        self.db = db
        self.table = table
        self.id = id
        self.name = name
        self.books = self._init_books()
        self.deleted = False
        self.cache = {
            "user": _user
        }

    def save(self) -> None:
        self.db.execute(
            "UPDATE "
            + self.table
            + " SET NAME = %(name)s WHERE ID = %(id)s",
            {"name": self.name, "id": self.id}
        )
        # TODO: ewww...
        self.db.execute(
            "DELETE FROM books_collections WHERE collection_id = %(id)s",
            {"id": self.id}
        )
        if(len(self.books) != 0):
            self.db.execute(
                "INSERT INTO books_collections (book_id, collection_id) VALUES" + ",".join([f"({book.id}, {self.id})" for book in self.books])
            )
        self.db.commit()

    def delete(self) -> None:
        self.db.execute("DELETE FROM books_collections WHERE collection_id = %(id)s", {"id": self.id})
        self.db.execute("DELETE FROM users_collections WHERE collection_id = %(id)s", {"id": self.id})
        self.db.execute("DELETE FROM " + self.table +
                        " WHERE id = %(id)s", {"id": self.id})
        self.db.commit()
        self.deleted = True

    def add_book(self, book: BookRecord) -> None:
        if(book not in self.books):
            self.books.append(book)
    
    def remove_book(self, book: BookRecord) -> bool:
        if(book in self.books):
            self.books.remove(book)
            return True
        return False

    @property
    def book_count(self) -> int:
        return self.db.execute("SELECT COUNT(*) FROM books_collections WHERE collection_id = %(id)s", {"id": self.id}).fetchone()[0]

    @property
    def page_count(self) -> int:
        return self.db.execute("SELECT SUM(length) FROM books WHERE id IN (SELECT book_id FROM books_collections WHERE collection_id = %(id)s)", {"id": self.id}).fetchone()[0]


    def _init_books(self) -> list[BookRecord]:
        cursor = self.db.execute(
            "SELECT * FROM books AS root WHERE id IN (SELECT book_id FROM books_collections WHERE collection_id = %(id)s)",
            {"id": self.id},
        )
        results = [
            BookRecord(self.db, "audiences", self.orm, *r)
            for r in cursor.fetchall()
        ]
        cursor.close()

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
    def create(cls, orm: ORM, name: str, ) -> Union["CollectionRecord", None]:
        # TODO: next_id is not safe. Maybe improve?
        next_id = ORM.next_available_id("collections")
        raise NotImplementedError