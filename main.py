from util import ApplicationContext
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer
from screens.login import LoginScreen
from screens.home import HomeScreen
from app_types import UserRecord

class BooksApp(App):
    CSS_PATH = ["./styles/login.screen.tcss", "./styles/app.tcss"]
    def __init__(self, context: ApplicationContext, driver_class = None, css_path = None, watch_css = False):
        super().__init__(driver_class, css_path, watch_css)
        self.context = context
        self.title = "Books Viewer"

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()

    def on_mount(self):
        self.install_screen(LoginScreen(), name="login")
        self.install_screen(HomeScreen(), name="home")
        self.push_screen("login")

    # Application Event Handling

    def on_login_screen_login_attempted(self, event: LoginScreen.LoginAttempted):
        if event.valid:
            self.notify("Logged in as " + event.email, title="Success", severity="information")
            self.push_screen("home")
        else:
            self.notify("Incorrect email/password", title="Failure", severity="error")

    def on_login_screen_account_created(self, event: LoginScreen.AccountCreated):
        try:
            new_user = UserRecord.create(self.context.orm, event.first_name, event.last_name, event.email, event.password)
        except:
            self.notify("Failed to create user (DB Error)", title="Failure", severity="error")
            return

        if self.context.login(event.email, event.password):
            self.notify("Created new account with email " + event.email, title="Success", severity="information")
            self.push_screen("home")
        else:
            self.notify("User created, but login failed.", title="Failure", severity="error")


if __name__ == "__main__":
    context = ApplicationContext()
    app = BooksApp(context)
    app.run()
    context.cleanup()