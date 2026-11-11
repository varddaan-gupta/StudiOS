from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDateEdit, QDialog, QHBoxLayout, QLabel, QLineEdit, QScrollArea, QStackedWidget,
    QVBoxLayout, QWidget,
)

from ... import config
from ..widgets import button, field, label


class SetupWizard(QDialog):
    """First-run setup: goal, modules, first courses."""

    def __init__(self, ctx, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        self.setWindowTitle("Welcome to StudiOS")
        self.setModal(True)
        self.setMinimumSize(620, 560)
        self.step = 0

        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 22, 28, 22)
        logo = QLabel()
        logo.setPixmap(QPixmap(str(config.ASSETS / "logo-wordmark.png")).scaledToHeight(34, Qt.SmoothTransformation))
        lay.addWidget(logo)
        self.heading = label("", "h1")
        self.sub = label("", muted=True, wrap=True)
        lay.addWidget(self.heading)
        lay.addWidget(self.sub)
        self.stack = QStackedWidget()
        lay.addWidget(self.stack, 1)
        nav = QHBoxLayout()
        self.back = button("Back", "ghost", self.prev)
        self.next = button("Next", "primary", self.advance)
        nav.addWidget(self.back)
        nav.addStretch(1)
        nav.addWidget(self.next)
        lay.addLayout(nav)

        self.stack.addWidget(self._page_goal())
        self.stack.addWidget(self._page_modules())
        self.stack.addWidget(self._page_courses())
        self._show()

    # ---- pages ----
    def _page_goal(self):
        w = QWidget()
        l = QVBoxLayout(w)
        self.name = QLineEdit(placeholderText="Your first name")
        self.exam = QComboBox(editable=True)
        self.exam.addItems(config.EXAMS)
        self.exam.setCurrentIndex(-1)
        self.exam.lineEdit().setPlaceholderText("Pick one or type your own")
        self.has_date = QCheckBox("I know my exam date")
        self.date = QDateEdit(QDate.currentDate().addMonths(6), calendarPopup=True)
        self.date.setEnabled(False)
        self.has_date.toggled.connect(self.date.setEnabled)
        for x in (field("What should we call you?", self.name), field("What are you preparing for?", self.exam),
                  self.has_date, self.date):
            l.addWidget(x)
        l.addStretch(1)
        return w

    def _page_modules(self):
        w = QWidget()
        l = QVBoxLayout(w)
        self.mods = {}
        for mid, text in config.MODULES[1:]:
            cb = QCheckBox(text)
            cb.setChecked(True)
            self.mods[mid] = cb
            l.addWidget(cb)
        l.addStretch(1)
        return w

    def _page_courses(self):
        w = QWidget()
        l = QVBoxLayout(w)
        self.rows = []
        holder = QWidget()
        self.rows_lay = QVBoxLayout(holder)
        self.rows_lay.setContentsMargins(0, 0, 0, 0)
        sc = QScrollArea()
        sc.setWidgetResizable(True)
        sc.setWidget(holder)
        l.addWidget(sc, 1)
        self.rows_lay.addStretch(1)
        self._add_row()
        l.addWidget(button("Add another course", "ghost", self._add_row))
        return w

    def _add_row(self):
        row = QWidget()
        r = QHBoxLayout(row)
        r.setContentsMargins(0, 0, 0, 6)
        title = QLineEdit(placeholderText="Course name")
        plat = QComboBox(editable=True)
        plat.addItems(config.PLATFORMS)
        url = QLineEdit(placeholderText="Link (https://...)")
        subj = QLineEdit(placeholderText="Subject")
        for x, s in ((title, 2), (plat, 2), (url, 3), (subj, 2)):
            r.addWidget(x, s)
        self.rows.append((title, plat, url, subj))
        self.rows_lay.insertWidget(self.rows_lay.count() - 1, row)

    # ---- flow ----
    def _show(self):
        heads = [("Let's set up your workspace", "Tell StudiOS what you are studying for."),
                 ("Choose your tools", "Switch off anything you will not use. You can change this in Settings."),
                 ("Add your courses", "Optional. Paste a link and StudiOS fetches the logo for your launcher.")]
        self.heading.setText(heads[self.step][0])
        self.sub.setText(heads[self.step][1])
        self.stack.setCurrentIndex(self.step)
        self.back.setVisible(self.step > 0)
        self.next.setText("Finish" if self.step == 2 else "Next")

    def advance(self):
        if self.step < 2:
            self.step += 1
            self._show()
        else:
            self.finish()

    def prev(self):
        self.step -= 1
        self._show()

    def finish(self):
        db = self.ctx.db
        db.set_profile(
            name=self.name.text().strip(), exam=self.exam.currentText().strip(),
            exam_date=self.date.date().toString("yyyy-MM-dd") if self.has_date.isChecked() else "",
            modules=["dashboard", *[m for m, cb in self.mods.items() if cb.isChecked()]], setup_complete=True)
        for title, plat, url, subj in self.rows:
            if title.text().strip():
                db.add("courses", title=title.text().strip(), platform=plat.currentText().strip(),
                       url=url.text().strip(), subject=subj.text().strip(), description="", progress=0)
        self.accept()

    def reject(self):
        pass  # first-run setup cannot be dismissed with Esc; Finish saves a profile
