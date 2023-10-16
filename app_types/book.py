from psycopg import Connection
from util.orm import Record, ORM
from datetime import datetime


class BookRecord(Record):
    def __init__(
        self,
        db: Connection,
        table: str,
        orm: ORM,
        id: int,
        title: str,
        length: int,
        edition: str,
        release_dt: datetime,
        isbn: int,
    ) -> None:
        super().__init__(db, table, orm)
        self.id = id
        self.title = title
        self.length = length
        self.edition = edition
        self.release_dt = release_dt
        self.isbn = isbn

    def save(self):
        self.db.execute(
            "UPDATE "
            + self.table
            + " SET title = %s, length = %s, edition = %s, release_dt = %s, isbn = %s WHERE id = %s",
            (
                self.title,
                self.length,
                self.edition,
                self.release_dt,
                self.isbn,
                self.id,
            ),
        )
        self.db.commit()

    def delete(self):
        self.db.execute("DELETE FROM " + self.table + " WHERE id = %s", (self.id,))
        self.db.commit()

    # Return an {id:name} mapping of audiences
    @property
    def audiences(self) -> dict[int, str]:
        cursor = self.db.execute("SELECT * FROM audiences AS root WHERE id IN (SELECT audience_id FROM books_audiences WHERE book_id = %(id)s)", {"id": self.id})
        results = {r[0]:r[1] for r in cursor.fetchall()}
        cursor.close()
        return results
    
    # Return an {id:name} mapping of genres
    @property
    def genres(self) -> dict[int, str]:
        cursor = self.db.execute("SELECT * FROM genres AS root WHERE id IN (SELECT genre_id FROM books_genres WHERE book_id = %(id)s)", {"id": self.id})
        results = {r[0]:r[1] for r in cursor.fetchall()}
        cursor.close()
        return results
