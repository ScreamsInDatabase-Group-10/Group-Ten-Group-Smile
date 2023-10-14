from textual.app import ComposeResult
from textual.widgets import Input, Header, Footer, Static, Button
from textual.containers import Container, Horizontal
from util import ContextScreen
import os

class LoginTitle(Static):
    def on_mount(self):
        self.update("[bold]Log In / Create Account[/]")

class LoginScreen(ContextScreen):
    CSS_PATH = os.path.join("..", "styles", "login.screen.tcss")

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            LoginTitle(id="login-title"),
            Input(placeholder="Email"),
            Input(placeholder="Password", password=True),
            Horizontal(
                Button("[bold]Log In[/bold]", id="login-btn-login", variant="primary"),
                Button("[bold]Create Account[/bold]", id="login-btn-create-account", variant="primary"),
                id="login-buttons"
            ),
            id="login-panel"
        )
        yield Footer()