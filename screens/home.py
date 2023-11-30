from textual.app import ComposeResult
from textual.widgets import Header, Footer, TabbedContent, TabPane
from util import ContextScreen
from textual.binding import Binding
from events.logout import LogoutMessage
from events.login import LoginMessage
from .panels import *


class HomeScreen(ContextScreen):
    # Bind CTRL + L to logout
    BINDINGS = [Binding("ctrl+l", "logout", "Log Out")]

    # Basic layout for the time being
    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        with TabbedContent(id="app-tabs"):
            with TabPane("Account", id="self"):
                yield SelfPanel()
            with TabPane("Books", id="books"):
                yield BooksPanel()
            with TabPane("Users", id="users"):
                yield UsersPanel()
            with TabPane("Recommendations", id="rec"):
                yield RecommendationPanel()

    # Listens for logout
    def action_logout(self):
        self.post_message(LogoutMessage())

    # Handle debug_autotab
    def handle_login(self, event: LoginMessage):
        if self.context.options.debug_autotab:
            tab_content: TabbedContent = self.query_one("#app-tabs")
            if tab_content:
                tab_content.active = self.context.options.debug_autotab
