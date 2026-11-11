from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QComboBox, QHBoxLayout, QLineEdit, QListWidget, QListWidgetItem, QPlainTextEdit, QVBoxLayout, QWidget,
)

from ..widgets import Panel, button, confirm, label, page_head
from .base import Page


class NotesPage(Page):
    scroll = False

    def setup(self):
        self.current = None
        self._loading = False
        self.save_timer = QTimer(self, singleShot=True, interval=500)
        self.save_timer.timeout.connect(self.save)

        self.root.addWidget(page_head("Notes", "Your own words are what the AI and the quizzes learn from.",
                                      button("New note", "primary", self.new)))
        row = QHBoxLayout()
        row.setSpacing(16)
        self.root.addLayout(row, 1)

        left = Panel()
        left.setFixedWidth(300)
        self.search = QLineEdit(placeholderText="Search notes")
        self.search.textChanged.connect(self.reload)
        self.subject_filter = QComboBox()
        self.subject_filter.currentIndexChanged.connect(self.reload)
        self.list = QListWidget()
        self.list.currentItemChanged.connect(self._picked)
        for w in (self.search, self.subject_filter, self.list):
            left.body.addWidget(w)
        row.addWidget(left)

        right = Panel()
        self.title = QLineEdit(placeholderText="Title")
        self.title.setStyleSheet("font-size:18px;font-weight:600;")
        self.subject = QComboBox(editable=True)
        self.subject.lineEdit().setPlaceholderText("Subject")
        self.course = QComboBox()
        self.body = QPlainTextEdit(placeholderText="Write or paste your notes here. They save automatically.")
        for w in (self.title, self.subject, self.course, self.body):
            (w.textChanged if hasattr(w, "textChanged") and not isinstance(w, QComboBox)
             else w.currentTextChanged).connect(self._dirty)
        meta = QHBoxLayout()
        meta.addWidget(self.subject, 1)
        meta.addWidget(self.course, 1)
        self.status = label("", muted=True)
        actions = QHBoxLayout()
        actions.addWidget(button("Ask AI about this", None, self.ask))
        actions.addWidget(button("Make quiz", None, self.quiz))
        actions.addStretch(1)
        actions.addWidget(self.status)
        actions.addWidget(button("Delete", "danger", self.delete))
        right.body.addWidget(self.title)
        right.body.addLayout(meta)
        right.body.addWidget(self.body, 1)
        right.body.addLayout(actions)
        row.addWidget(right, 1)
        self.editor_widgets = [self.title, self.subject, self.course, self.body]

    # ---- data ----
    def refresh(self):
        self.save()
        notes = self.db.list("notes")
        subjects = sorted({n.get("subject", "") for n in notes if n.get("subject")})
        self.subject_filter.blockSignals(True)
        self.subject_filter.clear()
        self.subject_filter.addItems(["All subjects", *subjects])
        self.subject_filter.blockSignals(False)
        self.subject.blockSignals(True)
        cur = self.subject.currentText()
        self.subject.clear()
        self.subject.addItems(subjects)
        self.subject.setCurrentText(cur)
        self.subject.blockSignals(False)
        self.course.blockSignals(True)
        self.course.clear()
        self.course.addItem("No course", "")
        for c in self.db.list("courses"):
            self.course.addItem(c["title"], c["id"])
        self.course.blockSignals(False)
        want = self.ctx.handoff.pop("note_id", None) or self.current
        self.reload(select=want)

    def reload(self, *_, select=None):
        select = select or self.current
        q = self.search.text().lower().strip()
        sf = self.subject_filter.currentText()
        self.list.blockSignals(True)
        self.list.clear()
        notes = sorted(self.db.list("notes"), key=lambda n: n["updated"], reverse=True)
        for n in notes:
            if sf != "All subjects" and n.get("subject") != sf:
                continue
            if q and q not in (n["title"] + n["body"]).lower():
                continue
            it = QListWidgetItem(f"{n['title'] or 'Untitled'}\n{n.get('subject', '') or 'No subject'}")
            it.setData(Qt.UserRole, n["id"])
            self.list.addItem(it)
            if n["id"] == select:
                self.list.setCurrentItem(it)
        self.list.blockSignals(False)
        item = self.list.currentItem()
        self._load(item.data(Qt.UserRole) if item else None)

    def _picked(self, item, _prev):
        self.save()
        self._load(item.data(Qt.UserRole) if item else None)

    def _load(self, note_id):
        self.current = note_id
        n = self.db.get("notes", note_id) if note_id else None
        self._loading = True
        for w in self.editor_widgets:
            w.setEnabled(n is not None)
        self.title.setText(n["title"] if n else "")
        self.subject.setCurrentText(n.get("subject", "") if n else "")
        idx = self.course.findData(n.get("course_id", "") if n else "")
        self.course.setCurrentIndex(max(idx, 0))
        self.body.setPlainText(n["body"] if n else "")
        self.status.setText("" if n else "Select or create a note")
        self._loading = False

    # ---- editing ----
    def _dirty(self, *_):
        if not self._loading and self.current:
            self.status.setText("Editing...")
            self.save_timer.start()

    def save(self):
        self.save_timer.stop()
        if not self.current or self._loading or not self.db.get("notes", self.current):
            return
        self.db.update("notes", self.current, title=self.title.text().strip(),
                       subject=self.subject.currentText().strip(), course_id=self.course.currentData() or "",
                       body=self.body.toPlainText())
        self.status.setText("Saved")

    def new(self):
        self.save()
        sf = self.subject_filter.currentText()
        n = self.db.add("notes", title="Untitled note", subject="" if sf == "All subjects" else sf,
                        course_id="", body="")
        self.current = n["id"]
        self.reload(select=n["id"])
        self.title.setFocus()
        self.title.selectAll()

    def delete(self):
        if self.current and confirm(self, "Delete this note?"):
            self.db.remove("notes", self.current)
            self.current = None
            self.reload()

    def ask(self):
        self.save()
        if self.current:
            self.ctx.go("assistant", note_ids=[self.current])

    def quiz(self):
        self.save()
        if self.current:
            self.ctx.go("revision", note_id=self.current)
