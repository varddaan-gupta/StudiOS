"""Start-up: splash, first-run wizard, main window."""
import sys

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFont, QIcon, QPixmap
from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget

from . import config
from .runtime import AppContext
from .ui.main_window import MainWindow
from .ui.theme import C, QSS
from .ui.pages.wizard import SetupWizard


class Splash(QWidget):
    """Boot sequence. Real checks, short lines."""

    def __init__(self):
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setFixedSize(460, 360)
        self.setObjectName("splash")
        self.setStyleSheet(f"#splash{{background:{C['ground']};border:1px solid {C['line2']};}}")
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignCenter)
        logo = QLabel()
        logo.setPixmap(QPixmap(str(config.ASSETS / "logo-mark.png")).scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo.setAlignment(Qt.AlignCenter)
        self.log = QLabel("")
        self.log.setFont(QFont("Cascadia Mono", 10))
        self.log.setStyleSheet(f"color:{C['muted']};")
        self.log.setMinimumHeight(90)
        self.log.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        lay.addWidget(logo)
        lay.addSpacing(18)
        lay.addWidget(self.log, 0, Qt.AlignHCenter)

    def line(self, text):
        self.log.setText((self.log.text() + "\n" + text).strip())


def run():
    app = QApplication(sys.argv)
    app.setApplicationName(config.APP_NAME)
    app.setWindowIcon(QIcon(str(config.ASSETS / "logo-mark.png")))
    app.setStyleSheet(QSS)

    splash = Splash()
    splash.show()
    ctx = AppContext()
    splash.line("> storage ........ ok")
    holder = {}

    def finish():
        win = MainWindow(ctx)
        holder["win"] = win
        splash.close()
        win.show()
        if not ctx.db.profile()["setup_complete"]:
            QTimer.singleShot(150, win.run_wizard)

    def got_status(s):
        splash.line("> ollama ......... " + ("ok" if s["running"] else "offline"))
        splash.line("> model .......... " + (s["active"] if s["model_ready"] else "not installed"))
        ctx.status_changed.disconnect(got_status)
        QTimer.singleShot(700, finish)

    ctx.status_changed.connect(got_status)
    QTimer.singleShot(350, lambda: splash.line("> interface ....... ok"))
    ctx.refresh_status()
    return app.exec()
