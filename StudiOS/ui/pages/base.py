from PySide6.QtWidgets import QVBoxLayout, QWidget

from ..widgets import clear_layout


class Page(QWidget):
    """Base for every module page.

    setup()    runs once  -> build widgets that keep state (editors, chats).
    refresh()  runs on every visit -> reload data from the database.
    scroll     True = the window wraps the page in a scroll area.
    """

    scroll = True

    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
        self.db = ctx.db
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(0, 0, 0, 0)
        self.root.setSpacing(0)
        self.setup()

    def setup(self):
        pass

    def refresh(self):
        pass

    def on_show(self):
        self.refresh()


class DynamicPage(Page):
    """Simple pages: rebuild the whole body from the database each visit. Implement build(layout)."""

    def setup(self):
        self.content = QWidget()
        self.cl = QVBoxLayout(self.content)
        self.cl.setContentsMargins(0, 0, 0, 0)
        self.cl.setSpacing(14)
        self.root.addWidget(self.content)

    def refresh(self):
        clear_layout(self.cl)
        self.build(self.cl)
        self.cl.addStretch(1)

    def build(self, layout):
        raise NotImplementedError
