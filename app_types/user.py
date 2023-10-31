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
