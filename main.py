from util import ApplicationContext
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer
from screens.login import LoginScreen
from screens.home import HomeScreen
from app_types import UserRecord
from events.logout import LogoutMessage
from events.login import LoginMessage
import os


# Main UI class
class BooksApp(App):
    # CSS paths
    CSS_PATH = [
        os.path.join("styles", "login.screen.tcss"),
        os.path.join("styles", "app.tcss"),
        os.path.join("styles", "home.screen.tcss"),
        os.path.join("styles", "self.panel.tcss"),
        os.path.join("styles", "books.panel.tcss"),
        os.path.join("styles", "users.panel.tcss"),
        os.path.join("styles", "pagination.util.tcss"),
        os.path.join("styles", "collection.panel.tcss"),
        os.path.join("styles", "rec.panel.tcss")
    ]

    # Dont use the command palette
    ENABLE_COMMAND_PALETTE = False

    # Setup
    def __init__(
        self,
        context: ApplicationContext,
        driver_class=None,
        css_path=None,
        watch_css=False,
    ):
        super().__init__(driver_class, css_path, watch_css)
        self.context = context
        self.title = "Books Viewer"

    # Just here because Textual seems to like it
    # Is never actually rendered
    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()

    # Setup screens & check autologin
    def on_mount(self):
        self.install_screen(LoginScreen(), name="login")
        self.install_screen(HomeScreen(), name="home")
        if self.context.options.debug_autologin:
            login_result = self.context.login(
                self.context.options.debug_autologin.email,
                self.context.options.debug_autologin.password,
            )
            if login_result:
                self.notify(
                    "Logged in as " + self.context.options.debug_autologin.email,
                    title="DEBUG SUCCESS",
                    severity="information",
                )
                self.push_screen("home")
                self.post_message(LoginMessage(self.context.logged_in))
            else:
                self.notify(
                    "Debug option failure: Autologin with {email} : {password}".format(
                        email=self.context.options.debug_autologin.email,
                        password=self.context.options.debug_autologin.password,
                    ),
                    title="DEBUG FAILURE",
                    severity="warning",
                )
                self.push_screen("login")
        else:
            self.push_screen("login")

    # Application Event Handling

    # Handle login attempt
    def on_login_screen_login_attempted(self, event: LoginScreen.LoginAttempted):
        if event.valid:
            self.notify(
                "Logged in as " + event.email, title="Success", severity="information"
            )
            self.push_screen("home")
            self.post_message(LoginMessage(self.context.logged_in))
        else:
            self.notify("Incorrect email/password", title="Failure", severity="error")

    # Handle account creation
    def on_login_screen_account_created(self, event: LoginScreen.AccountCreated):
        try:
            new_user = UserRecord.create(
                self.context.orm,
                event.first_name,
                event.last_name,
                event.email,
                event.password,
            )
        except:
            self.notify(
                "Failed to create user (DB Error)", title="Failure", severity="error"
            )
            return

        try:
            if self.context.login(event.email, event.password):
                self.notify(
                    "Created new account with email " + event.email,
                    title="Success",
                    severity="information",
                )
                self.push_screen("home")
                self.post_message(LoginMessage(self.context.logged_in))
            else:
                self.notify(
                    "User created, but login failed.", title="Failure", severity="error"
                )
        except:
            self.notify(
                "Failed to create user (DB Error)", title="Failure", severity="error"
            )
            return

    # Handle logout
    def on_logout_message(self, event: LogoutMessage):
        self.context.logout()
        self.push_screen("login")

    def on_login_message(self, event: LoginMessage):
        home_screen: HomeScreen = self.get_screen("home")
        home_screen.handle_login(event)


if __name__ == "__main__":
    context = ApplicationContext()
    app = BooksApp(context)
    app.run()
    context.cleanup()
