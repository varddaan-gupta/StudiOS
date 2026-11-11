from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFormLayout, QGridLayout, QHBoxLayout, QLineEdit,
    QPlainTextEdit, QSlider, QVBoxLayout,
)

from ... import config
from ..widgets import Panel, button, confirm, course_icon, label, meter, page_head
from .base import DynamicPage


class CourseDialog(QDialog):
    def __init__(self, parent, course=None):
        super().__init__(parent)
        c = course or {}
        self.setWindowTitle("Edit course" if course else "Add course")
        self.setMinimumWidth(460)
        self.title = QLineEdit(c.get("title", ""))
        self.subject = QComboBox(editable=True)
        self.subject.addItems(config.SUBJECTS)
        self.subject.setCurrentText(c.get("subject", ""))
        self.platform = QComboBox(editable=True)
        self.platform.addItems(config.PLATFORMS)
        self.platform.setCurrentText(c.get("platform", ""))
        self.url = QLineEdit(c.get("url", ""))
        self.url.setPlaceholderText("https://youtube.com/playlist?list=...")
        self.desc = QPlainTextEdit(c.get("description", ""))
        self.desc.setFixedHeight(70)
        self.progress = QSlider(Qt.Horizontal)
        self.progress.setRange(0, 100)
        self.progress.setValue(c.get("progress", 0))
        self.pct = label(f"{self.progress.value()}%", muted=True)
        self.progress.valueChanged.connect(lambda v: self.pct.setText(f"{v}%"))
        form = QFormLayout()
        form.setSpacing(10)
        form.addRow("Course name", self.title)
        form.addRow("Subject", self.subject)
        form.addRow("Platform", self.platform)
        form.addRow("Link", self.url)
        form.addRow("Notes", self.desc)
        prow = QHBoxLayout()
        prow.addWidget(self.progress, 1)
        prow.addWidget(self.pct)
        form.addRow("Topics completed", prow)
        bb = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        bb.accepted.connect(self._ok)
        bb.rejected.connect(self.reject)
        lay = QVBoxLayout(self)
        lay.addLayout(form)
        lay.addWidget(bb)
        self.err = label("", chip=None)
        lay.addWidget(self.err)

    def _ok(self):
        if not self.title.text().strip():
            self.err.setText("Give the course a name.")
            return
        self.accept()

    def values(self):
        return dict(title=self.title.text().strip(), subject=self.subject.currentText().strip(),
                    platform=self.platform.currentText().strip(), url=self.url.text().strip(),
                    description=self.desc.toPlainText().strip(), progress=self.progress.value())


class CoursesPage(DynamicPage):
    def build(self, layout):
        layout.addWidget(page_head(
            "Courses", "One launcher for every playlist, portal and class you follow.",
            button("Add course", "primary", self.add)))
        courses = self.db.list("courses")
        if not courses:
            p = Panel()
            p.body.addWidget(label("No courses yet. Add one with a link and StudiOS fetches its logo.", muted=True))
            layout.addWidget(p)
            return
        grid = QGridLayout()
        grid.setSpacing(16)
        for i in range(3):
            grid.setColumnStretch(i, 1)
        for i, c in enumerate(courses):
            grid.addWidget(self._card(c), i // 3, i % 3)
        layout.addLayout(grid)

    def _card(self, c):
        p = Panel()
        head = QHBoxLayout()
        head.setSpacing(12)
        head.addWidget(course_icon(self.ctx, c))
        col = QVBoxLayout()
        col.setSpacing(0)
        col.addWidget(label(c["title"], "h2", wrap=True))
        col.addWidget(label(" · ".join(x for x in [c.get("subject"), c.get("platform")] if x) or "No subject",
                            muted=True))
        head.addLayout(col, 1)
        p.body.addLayout(head)
        if c.get("description"):
            p.body.addWidget(label(c["description"][:120], muted=True, wrap=True))
        p.body.addWidget(meter(c.get("progress", 0)))
        p.body.addWidget(label(f"{c.get('progress', 0)}% of topics done", muted=True))
        row = QHBoxLayout()
        row.setSpacing(6)
        open_btn = button("Open", "primary", lambda u=c.get("url"): self.open(u), "sm")
        open_btn.setEnabled(bool(c.get("url")))
        row.addWidget(open_btn)
        row.addWidget(button("Ask AI", None, lambda cid=c["id"]: self.ctx.go("assistant", course_id=cid), "sm"))
        row.addStretch(1)
        row.addWidget(button("Edit", "ghost", lambda cc=c: self.edit(cc), "sm"))
        row.addWidget(button("Delete", "ghost", lambda cc=c: self.delete(cc), "sm"))
        p.body.addLayout(row)
        return p

    def open(self, url):
        if url:
            QDesktopServices.openUrl(QUrl(url if "://" in url else "https://" + url))

    def add(self):
        d = CourseDialog(self)
        if d.exec():
            self.db.add("courses", **d.values())
            self.ctx.data_changed.emit("courses")
            self.refresh()

    def edit(self, c):
        d = CourseDialog(self, c)
        if d.exec():
            self.db.update("courses", c["id"], **d.values())
            self.ctx.data_changed.emit("courses")
            self.refresh()

    def delete(self, c):
        if confirm(self, f"Delete course \"{c['title']}\"?"):
            self.db.remove("courses", c["id"])
            self.ctx.data_changed.emit("courses")
            self.refresh()
