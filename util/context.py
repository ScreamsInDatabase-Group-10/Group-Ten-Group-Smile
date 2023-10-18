from dataclasses import dataclass
from dotenv import load_dotenv
from psycopg import Connection, connect
from sshtunnel import SSHTunnelForwarder
from os import getenv, environ
from typing import Optional, Literal
from .orm import ORM
from .search import search_internal, SearchCondition
from app_types import *
from datetime import datetime
from time import time

load_dotenv()


# Database options from ENV
@dataclass
class DatabaseOptions:
    host: str
    port: int
    username: str
    password: str
    database: str

    tunnelled: bool
    tunnel_host: Optional[str]
    tunnel_port: Optional[int]
    tunnel_username: Optional[str]
    tunnel_password: Optional[str]


# Database AutoLogin options from ENV
@dataclass
class DebugAutologin:
    email: str
    password: str


# Main options class from ENV
@dataclass
class ContextOptions:
    database: DatabaseOptions
    debug_autologin: Optional[DebugAutologin]
    debug_autotab: Optional[Literal["self", "books", "users"]]


# Centralized application context class
class ApplicationContext:
    def __init__(self) -> None:
        self.options: ContextOptions = self.parse_options()
        self.db, self.tunnel = self.open_database()
        self.orm: ORM = ORM(self.db)
        self.orm.register("books", BookRecord)
        self.orm.register("users", UserRecord)
        self.logged_in: Optional[UserRecord] = None
        print(BookRecord.search(self.orm, audience="children", pagination={"limit": 10}))

    # Parse options from environment variables
    def parse_options(self) -> ContextOptions:
        tunnelled = getenv("DB_TUNNEL", "false") == "true"
        return ContextOptions(
            database=DatabaseOptions(
                host=environ["DB_IP"],
                port=int(getenv("DB_PORT", "5432")),
                username=environ["DB_USER"],
                password=environ["DB_PASSWORD"],
                database=environ["DB_DATABASE"],
                tunnelled=tunnelled,
                tunnel_host=environ["DB_TUNNEL_ADDR"] if tunnelled else None,
                tunnel_port=int(getenv("DB_TUNNEL_PORT", "5432"))
                if tunnelled
                else None,
                tunnel_username=environ["DB_TUNNEL_USERNAME"] if tunnelled else None,
                tunnel_password=environ["DB_TUNNEL_PASSWORD"] if tunnelled else None,
            ),
            debug_autologin=DebugAutologin(
                email=environ["DEBUG_AUTOLOGIN_EMAIL"],
                password=environ["DEBUG_AUTOLOGIN_PASSWORD"],
            )
            if getenv("DEBUG_FLAG_AUTOLOGIN", "false") == "true"
            else None,
            debug_autotab=environ["DEBUG_AUTOTAB_NAME"]
            if getenv("DEBUG_FLAG_AUTOTAB", "false") == "true"
            else None,
        )

    # Activate database from ENV options
    def open_database(self) -> tuple[Connection, Optional[SSHTunnelForwarder]]:
        if self.options.database.tunnelled:
            tunnel = SSHTunnelForwarder(
                (self.options.database.tunnel_host, self.options.database.tunnel_port),
                ssh_username=self.options.database.tunnel_username,
                ssh_password=self.options.database.tunnel_password,
                remote_bind_address=(
                    self.options.database.host,
                    self.options.database.port,
                ),
            )
            tunnel.start()
            connection = connect(
                dbname=self.options.database.database,
                user=self.options.database.username,
                password=self.options.database.password,
                host=tunnel.local_bind_host,
                port=tunnel.local_bind_port,
            )
            return connection, tunnel

        else:
            connection = connect(
                dbname=self.options.database.database,
                user=self.options.database.username,
                password=self.options.database.password,
                host=self.options.database.host,
                port=self.options.database.port,
            )
            return connection, None

    # Cleanup database & SSH tunnel
    def cleanup(self):
        self.db.commit()
        self.db.close()
        if self.tunnel:
            self.tunnel.stop()

    # Check login, then perform login tasks if correct
    def login(self, email: str, password: str) -> bool:
        email_result: list[UserRecord] = self.orm.get_records_by_query_suffix(
            "users",
            "WHERE email = %(email)s AND password = %(password)s",
            {"email": email, "password": password},
        )
        if len(email_result) != 0:
            self.logged_in = email_result[0]
            email_result[0].access_dt = datetime.fromtimestamp(time()).isoformat()
            email_result[0].save()
            return True
        else:
            self.logged_in = None
            return False

    # Logs out, just a semantic helper
    def logout(self):
        self.logged_in = None
