from psycopg import Connection
from util.orm import Record, ORM, SearchResult, SearchCondition, PaginationParams, search_internal
from datetime import datetime
from typing import Literal, Optional

class AudienceRecord(Record):
    def __init__(self, db: Connection, table: str, orm: ORM, id: int, name: str, *args) -> None:
        super().__init__(db, table, orm, *args)
        self.id = id
        self.name = name

class GenreRecord(Record):
    def __init__(self, db: Connection, table: str, orm: ORM, id: int, name: str, *args) -> None:
        super().__init__(db, table, orm, *args)
        self.id = id
        self.name = name


class ContributorRecord(Record):
    def __init__(
        self,
        db: Connection,
        table: str,
        orm: ORM,
        type: Literal["author", "publisher", "editor"],
        id: int,
        first_name: str,
        last_name_or_company: str,
        *args,
    ) -> None:
        super().__init__(db, table, orm, *args)
        self.type = type
        self.id = id
        self.first_name = first_name
        self.last_name_or_company = last_name_or_company

    @property
    def name(self) -> str:
        if self.type == "publisher":
            return self.last_name_or_company.title()
        return (self.first_name + " " + self.last_name_or_company).title()

    @property
    def books(self) -> list["BookRecord"]:
        match self.type:
            case "author":
                relation_table = "books_authors"
            case "editor":
                relation_table = "books_editors"
            case "publisher":
                relation_table = "books_publishers"

        cursor = self.db.execute(
            "SELECT * FROM books AS root WHERE id IN (SELECT book_id FROM {rel} WHERE contributor_id = %(id)s)".format(
                rel=relation_table
            ),
            {"id": self.id},
        )
        results = [
            BookRecord(self.db, "books", self.orm, *r) for r in cursor.fetchall()
        ]
        cursor.close()
        return results

    def save(self):
        self.db.execute(
            "UPDATE "
            + self.table
            + " SET name_first = %s, name_last_company = %s WHERE id = %s",
            (
                self.first_name,
                self.last_name_or_company,
                self.id,
            ),
        )
        self.db.commit()

    def delete(self):
        self.db.execute("DELETE FROM " + self.table + " WHERE id = %s", (self.id,))
        self.db.commit()


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
        _authors: list[ContributorRecord] = None,
        _editors: list[ContributorRecord] = None,
        _publishers: list[ContributorRecord] = None,
        _audiences: list[AudienceRecord] = None,
        _genres: list[GenreRecord] = None
    ) -> None:
        super().__init__(db, table, orm)
        self.id = id
        self.title = title
        self.length = length
        self.edition = edition
        self.release_dt = release_dt
        self.isbn = isbn
        self.cache = {
            "authors": _authors,
            "editors": _editors,
            "publishers": _publishers,
            "audiences": _audiences,
            "_genres": _genres
        }

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

    # Return a list of AudienceRecord
    @property
    def audiences(self) -> list[AudienceRecord]:
        if self.cache["audiences"]:
            return self.cache["audiences"]
        cursor = self.db.execute(
            "SELECT * FROM audiences AS root WHERE id IN (SELECT audience_id FROM books_audiences WHERE book_id = %(id)s)",
            {"id": self.id},
        )
        results = [AudienceRecord(self.db, "audiences", self.orm, *r) for r in cursor.fetchall()]
        self.cache["audiences"] = results
        cursor.close()
        return results

    # Return a list of GenreRecord
    @property
    def genres(self) -> list[GenreRecord]:
        if self.cache["genres"]:
            return self.cache["genres"]
        cursor = self.db.execute(
            "SELECT * FROM genres AS root WHERE id IN (SELECT genre_id FROM books_genres WHERE book_id = %(id)s)",
            {"id": self.id},
        )
        results = [GenreRecord(self.db, "genres", self.orm, *r) for r in cursor.fetchall()]
        self.cache["genres"] = results
        cursor.close()
        return results

    @property
    def authors(self) -> list[ContributorRecord]:
        if self.cache["authors"]:
            return self.cache["authors"]
        cursor = self.db.execute(
            "SELECT * FROM contributors AS root WHERE id IN (SELECT contributor_id FROM books_authors WHERE book_id = %(id)s)",
            {"id": self.id},
        )
        results = [
            ContributorRecord(self.db, "contributors", self.orm, "author", *r)
            for r in cursor.fetchall()
        ]
        self.cache["authors"] = results
        cursor.close()
        return results

    @property
    def editors(self) -> list[ContributorRecord]:
        if self.cache["editors"]:
            return self.cache["editors"]
        cursor = self.db.execute(
            "SELECT * FROM contributors AS root WHERE id IN (SELECT contributor_id FROM books_editors WHERE book_id = %(id)s)",
            {"id": self.id},
        )
        results = [
            ContributorRecord(self.db, "contributors", self.orm, "editor", *r)
            for r in cursor.fetchall()
        ]
        self.cache["editors"] = results
        cursor.close()
        return results

    @property
    def publishers(self) -> list[ContributorRecord]:
        if self.cache["publishers"]:
            return self.cache["publishers"]
        cursor = self.db.execute(
            "SELECT * FROM contributors AS root WHERE id IN (SELECT contributor_id FROM books_publishers WHERE book_id = %(id)s)",
            {"id": self.id},
        )
        results = [
            ContributorRecord(self.db, "contributors", self.orm, "publisher", *r)
            for r in cursor.fetchall()
        ]
        self.cache["publishers"] = results
        cursor.close()
        return results

    @classmethod
    def search(
        self,
        orm: ORM,
        pagination: PaginationParams,
        title: Optional[str] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        edition: Optional[str] = None,
        released_after: Optional[datetime] = None,
        released_before: Optional[datetime] = None,
        isbn: Optional[int] = None,
        author_name: Optional[str] = None,
        genre: Optional[str] = None,
        audience: Optional[str] = None,
    ) -> SearchResult:
        fields = []
        if title != None:
            fields.append(
                SearchCondition(
                    "title ilike %s",
                    ["%%" + title + "%%"],
                )
            )
        if min_length != None:
            fields.append(SearchCondition("length >= %s", [min_length]))
        if max_length != None:
            fields.append(SearchCondition("length <= %s", [max_length]))
        if edition != None:
            fields.append(SearchCondition("edition ilike %s", ["%%" + edition + "%%"]))
        if released_after != None:
            fields.append(SearchCondition("release_dt >= %s", [released_after]))
        if released_before != None:
            fields.append(SearchCondition("release_dt <= %s", [released_before]))
        if isbn != None:
            fields.append(SearchCondition("isbn = %s", [isbn]))
        if author_name != None:
            fields.append(
                SearchCondition(
                    "id IN (SELECT book_id FROM books_authors AS aus WHERE contributor_id IN (SELECT id FROM contributors WHERE name_last_company ilike %s OR name_first ilike %s OR name_first || ' ' || name_last_company ilike %s))",
                    [
                        "%%" + author_name + "%%",
                        "%%" + author_name + "%%",
                        "%%" + author_name + "%%",
                    ],
                )
            )
        if genre != None:
            fields.append(
                SearchCondition(
                    "id IN (SELECT book_id FROM books_genres AS ges WHERE genre_id IN (SELECT id FROM genres WHERE name ilike %s))",
                    ["%%" + genre + "%%"],
                )
            )

        if audience != None:
            fields.append(
                SearchCondition(
                    "id IN (SELECT book_id FROM books_audiences AS ges WHERE audience_id IN (SELECT id FROM audiences WHERE name ilike %s))",
                    ["%%" + audience + "%%"],
                )
            )
        return search_internal(
            orm,
            "books",
            BookRecord,
            fields,
            pagination.get("order") if pagination else None,
            pagination.get("offset") if pagination else None,
            pagination.get("limit") if pagination else None,
        )
