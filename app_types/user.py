from psycopg import Connection
from util.orm import Record, ORM
from datetime import datetime
import time
from typing import Union


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
