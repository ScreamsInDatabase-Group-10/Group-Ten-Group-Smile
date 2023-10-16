from textual.app import ComposeResult
from textual.widgets import Header, Footer
from util import ContextScreen
from textual.binding import Binding
from events.logout import LogoutMessage

class HomeScreen(ContextScreen):
    # Bind CTRL + L to logout
    BINDINGS = [
        Binding("ctrl+l", "logout", "Log Out")
    ]

    # Basic layout for the time being
    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()

    # Listens for logout
    def action_logout(self):
        self.post_message(LogoutMessage())