from psycopg import Connection
from util.orm import Record, ORM
from datetime import datetime
from typing import Literal

class ContributorRecord(Record):
    def __init__(self, db: Connection, table: str, orm: ORM, type: Literal["author", "publisher", "editor"], id: int, first_name: str, last_name_or_company: str, *args) -> None:
        super().__init__(db, table, orm, *args)
        self.type = type
        self.id = id
        self.first_name = first_name
        self.last_name_or_company = last_name_or_company

    @property
    def name(self):
        if self.type == "publisher":
            return self.last_name_or_company.title()
        return (self.first_name + " " + self.last_name_or_company).title()
    
    @property
    def books(self):
        match self.type:
            case "author":
                relation_table = "books_authors"
            case "editor":
                relation_table = "books_editors"
            case "publisher":
                relation_table = "books_publishers"
        


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
    
    @property
    def authors(self) -> list[ContributorRecord]:
        cursor = self.db.execute("SELECT * FROM contributors AS root WHERE id IN (SELECT contributor_id FROM books_authors WHERE book_id = %(id)s)", {"id": self.id})
        results = [ContributorRecord(self.db, "contributors", self.orm, "author", *r) for r in cursor.fetchall()]
        cursor.close()
        return results

    @property
    def editors(self) -> list[ContributorRecord]:
        cursor = self.db.execute("SELECT * FROM contributors AS root WHERE id IN (SELECT contributor_id FROM books_editors WHERE book_id = %(id)s)", {"id": self.id})
        results = [ContributorRecord(self.db, "contributors", self.orm, "editor", *r) for r in cursor.fetchall()]
        cursor.close()
        return results
    
    @property
    def publishers(self) -> list[ContributorRecord]:
        cursor = self.db.execute("SELECT * FROM contributors AS root WHERE id IN (SELECT contributor_id FROM books_publishers WHERE book_id = %(id)s)", {"id": self.id})
        results = [ContributorRecord(self.db, "contributors", self.orm, "publisher", *r) for r in cursor.fetchall()]
        cursor.close()
        return results
