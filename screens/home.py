from textual.app import ComposeResult
from textual.widgets import Header, Footer
from util import ContextScreen
from textual.binding import Binding
from events.logout import LogoutMessage

class HomeScreen(ContextScreen):
    BINDINGS = [
        Binding("ctrl+l", "logout", "Log Out")
    ]
    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()

    def action_logout(self):
        self.post_message(LogoutMessage())