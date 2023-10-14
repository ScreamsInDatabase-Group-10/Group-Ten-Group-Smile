from util import ApplicationContext
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer
from screens.login import LoginScreen

class BooksApp(App):
    CSS_PATH = ["./styles/login.screen.tcss"]
    def __init__(self, context: ApplicationContext, driver_class = None, css_path = None, watch_css = False):
        super().__init__(driver_class, css_path, watch_css)
        self.context = context
        self.title = "Books Viewer"

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()

    def on_mount(self):
        self.install_screen(LoginScreen(), name="login")
        self.push_screen("login")

if __name__ == "__main__":
    context = ApplicationContext()
    app = BooksApp(context)
    app.run()
    context.cleanup()