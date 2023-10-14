from util import ApplicationContext
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer

class BooksApp(App):
    def __init__(self, context: ApplicationContext, driver_class = None, css_path = None, watch_css = False):
        super().__init__(driver_class, css_path, watch_css)
        self.context = context

    def compose(self) -> ComposeResult:
        yield Header(name="Books Viewer")
        yield Footer()

if __name__ == "__main__":
    context = ApplicationContext()
    app = BooksApp(context)
    app.run()
    context.cleanup()