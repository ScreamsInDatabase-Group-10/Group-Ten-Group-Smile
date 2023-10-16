from rich.console import RenderableType
from textual.app import ComposeResult
from textual.widgets import Input, Header, Footer, Static, Button, Input
from textual.containers import Container, Horizontal
from textual.reactive import reactive
from util import ContextScreen
import os


class LoginTitle(Static):
    def on_mount(self):
        self.update("[bold]Log In / Create Account[/]")



class LoginScreen(ContextScreen):
    CSS_PATH = os.path.join("..", "styles", "login.screen.tcss")
    login_valid = reactive(False)
    ca_valid = reactive(False)

    def __init__(self, name=None, id=None, classes=None) -> None:
        super().__init__(name, id, classes)
        self.inputs = {"email": "", "password": "", "first_name": "", "last_name": ""}
        self.creating_account = False

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            LoginTitle(id="login-title"),
            Input(placeholder="Email", id="login-email", name="email"),
            Input(placeholder="Password", password=True, id="login-password", name="password"),
            Container(
                Input(placeholder="First Name", id="ca-first-name", name="first_name"),
                Input(placeholder="Last Name", id="ca-last-name", name="last_name"),
                id="create-account-container",
                classes="hidden",
            ),
            Horizontal(
                Button("[bold]Log In[/bold]", id="login-btn-login", variant="primary", disabled=True),
                Button(
                    "[bold]Create Account[/bold]",
                    id="login-btn-create-account",
                    variant="primary",
                    disabled=True
                ),
                id="login-buttons",
            ),
            id="login-panel",
        )
        yield Footer()

    def watch_login_valid(self, old: bool, new: bool):
        self.query_one("#login-btn-login").disabled = not new
    
    def watch_ca_valid(self, old: bool, new: bool):
        self.query_one("#login-btn-create-account").disabled = not new

    def on_input_changed(self, event: Input.Changed):
        if event.input.name in self.inputs.keys():
            self.inputs[event.input.name] = event.input.value
        
        if len(self.inputs["email"]) == 0 or len(self.inputs["password"]) == 0:
            self.login_valid = False
            self.ca_valid = False
        else:
            self.login_valid = True
            if self.creating_account:
                if len(self.inputs["first_name"]) > 0 and len(self.inputs["last_name"]) > 0:
                    self.ca_valid = True
                else:
                    self.ca_valid = False
            else:
                self.ca_valid = True

    def on_button_pressed(self, event: Button.Pressed):
        match event.button.id:
            case "login-btn-login":
                self.log.debug(self.inputs)
            case "login-btn-create-account":
                widget = self.query_one("#create-account-container")
                if "hidden" in widget.classes:
                    widget.remove_class("hidden")
                    self.query_one("#login-btn-login").add_class("hidden")
                    self.query_one("#login-panel").add_class("expanded")
                    self.query_one("#login-btn-create-account").add_class("expanded")
                    self.creating_account = True
                    self.ca_valid = False
                else:
                    self.log.debug(self.inputs)
