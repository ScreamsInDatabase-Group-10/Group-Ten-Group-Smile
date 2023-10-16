from textual.app import ComposeResult
from textual.widgets import Header, Footer, TabbedContent, TabPane
from util import ContextScreen
from textual.binding import Binding
from events.logout import LogoutMessage
from .panels import *

class HomeScreen(ContextScreen):
    # Bind CTRL + L to logout
    BINDINGS = [
        Binding("ctrl+l", "logout", "Log Out")
    ]

    # Basic layout for the time being
    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        with TabbedContent():
            with TabPane("Account"):
                yield SelfPanel()
            with TabPane("Books"):
                yield BooksPanel()
            with TabPane("Users"):
                yield UsersPanel()

    # Listens for logout
    def action_logout(self):
        self.post_message(LogoutMessage())