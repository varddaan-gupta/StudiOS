from datetime import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QMainWindow, QScrollArea, QStackedWidget, QToolButton, QVBoxLayout, QWidget,
)

from .. import config
from .pages import PAGES
from .pages.wizard import SetupWizard
from .widgets import DotGrid, button, clear_layout, dock_icon, label


class MainWindow(QMainWindow):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
        self.buttons = {}
        self.setWindowTitle("StudiOS")
        self.resize(1320, 840)
        self.setMinimumSize(1080, 700)

        root = QWidget()
        self.setCentralWidget(root)
        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # dock
        dock = QWidget()
        dock.setObjectName("dockBar")
        dock.setFixedWidth(92)
        dock.setStyleSheet("#dockBar{border-right:1px solid #262b47;}")
        dl = QVBoxLayout(dock)
        dl.setContentsMargins(8, 14, 8, 14)
        dl.setSpacing(2)
        mark = QLabel()
        mark.setPixmap(QPixmap(str(config.ASSETS / "logo-mark.png")).scaled(46, 46, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        mark.setAlignment(Qt.AlignCenter)
        dl.addWidget(mark)
        dl.addSpacing(12)
        self.nav_box = QVBoxLayout()
        self.nav_box.setSpacing(2)
        dl.addLayout(self.nav_box)
        dl.addStretch(1)
        self.settings_btn = self._dock_button("settings")
        dl.addWidget(self.settings_btn)
        outer.addWidget(dock)

        # right side
        right = QVBoxLayout()
        right.setSpacing(0)
        outer.addLayout(right, 1)
        top = QWidget()
        top.setObjectName("topBar")
        top.setFixedHeight(58)
        top.setStyleSheet("#topBar{border-bottom:1px solid #262b47;}")
        tl = QHBoxLayout(top)
        tl.setContentsMargins(24, 0, 24, 0)
        word = QLabel()
        word.setPixmap(QPixmap(str(config.ASSETS / "logo-wordmark.png")).scaledToHeight(28, Qt.SmoothTransformation))
        tl.addWidget(word)
        tl.addStretch(1)
        self.exam_chip = label("", chip="accent")
        self.ai_pill = button("AI: checking...", None, lambda: self.go("settings"))
        self.ai_pill.setObjectName("aiPill")
        self.clock = label("", "mono", muted=True)
        tl.addWidget(self.exam_chip)
        tl.addWidget(self.ai_pill)
        tl.addWidget(self.clock)
        right.addWidget(top)

        self.field = DotGrid()
        fl = QVBoxLayout(self.field)
        fl.setContentsMargins(30, 24, 30, 20)
        self.stack = QStackedWidget()
        fl.addWidget(self.stack)
        right.addWidget(self.field, 1)

        # pages are created lazily on first visit
        self.pages, self.holders = {}, {}
        self.toast_lbl = QLabel(self.field)
        self.toast_lbl.setStyleSheet("background:#1a1e35;border:1px solid #343a5e;border-left:3px solid #7c8cff;"
                                     "border-radius:8px;padding:9px 14px;")
        self.toast_lbl.hide()
        self.toast_timer = QTimer(self, singleShot=True, interval=3500)
        self.toast_timer.timeout.connect(self.toast_lbl.hide)

        ctx.navigate.connect(self.go)
        ctx.status_changed.connect(self.on_status)
        ctx.data_changed.connect(self.on_data)
        ctx.toast.connect(self.show_toast)
        ctx.wizard_requested.connect(self.run_wizard)

        self.build_dock()
        self.on_data("profile")
        self.tick()
        for timer, ms, fn in ((QTimer(self), 30_000, self.tick), (QTimer(self), 15_000, ctx.refresh_status)):
            timer.timeout.connect(fn)
            timer.start(ms)
        ctx.refresh_status()
        self.go("dashboard")

    # ---- dock ----
    def _dock_button(self, pid):
        b = QToolButton()
        b.setObjectName("dock")
        b.setText(PAGES[pid][0])
        b.setIcon(dock_icon(pid))
        b.setIconSize(b.iconSize() * 1.4)
        b.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        b.setCheckable(True)
        b.setAutoExclusive(True)
        b.setCursor(Qt.PointingHandCursor)
        b.setFixedHeight(66)
        b.clicked.connect(lambda _=False, p=pid: self.go(p))
        self.buttons[pid] = b
        return b

    def build_dock(self):
        enabled = self.ctx.db.profile()["modules"]
        clear_layout(self.nav_box)
        for pid in PAGES:
            if pid == "settings":
                continue
            if pid in enabled or pid == "dashboard":
                btn = self.buttons.get(pid) or self._dock_button(pid)
                self.nav_box.addWidget(btn)
        for pid, b in self.buttons.items():  # drop buttons for disabled modules
            if pid != "settings" and pid not in enabled and pid != "dashboard":
                b.hide()
            else:
                b.show()

    # ---- navigation ----
    def go(self, pid):
        if pid not in PAGES:
            return
        if pid not in self.pages:
            page = PAGES[pid][1](self.ctx)
            self.pages[pid] = page
            holder = QWidget()
            hl = QVBoxLayout(holder)
            hl.setContentsMargins(0, 0, 0, 0)
            if page.scroll:
                sc = QScrollArea()
                sc.setWidgetResizable(True)
                sc.setFrameShape(QScrollArea.NoFrame)
                sc.viewport().setAutoFillBackground(False)
                sc.setWidget(page)
                hl.addWidget(sc)
            else:
                hl.addWidget(page)
            self.stack.addWidget(holder)
            self.holders[pid] = holder
        self.stack.setCurrentWidget(self.holders[pid])
        self.pages[pid].on_show()
        if pid in self.buttons:
            self.buttons[pid].setChecked(True)

    # ---- live bits ----
    def on_status(self, s):
        if s["running"] and s["model_ready"]:
            self.ai_pill.setText(f"AI ready  ·  {s['active']}")
            self.ai_pill.setStyleSheet("color:#5fd3a0;border:1px solid #2c6b52;border-radius:14px;padding:4px 14px;")
        elif s["running"]:
            self.ai_pill.setText("AI: no model installed")
            self.ai_pill.setStyleSheet("color:#f2b75c;border:1px solid #7a5d2a;border-radius:14px;padding:4px 14px;")
        else:
            self.ai_pill.setText("AI offline")
            self.ai_pill.setStyleSheet("color:#ff6b7a;border:1px solid #7a3340;border-radius:14px;padding:4px 14px;")

    def on_data(self, what):
        if what == "profile":
            p = self.ctx.db.profile()
            self.exam_chip.setText(p["exam"])
            self.exam_chip.setVisible(bool(p["exam"]))
            self.build_dock()

    def tick(self):
        self.clock.setText(datetime.now().strftime("%a %d %b  %H:%M"))

    def show_toast(self, text):
        self.toast_lbl.setText(text)
        self.toast_lbl.adjustSize()
        self.toast_lbl.move(self.field.width() - self.toast_lbl.width() - 24, self.field.height() - self.toast_lbl.height() - 20)
        self.toast_lbl.show()
        self.toast_lbl.raise_()
        self.toast_timer.start()

    def run_wizard(self):
        SetupWizard(self.ctx, self).exec()
        self.on_data("profile")
        for page in self.pages.values():
            page.refresh()
        self.go("dashboard")
