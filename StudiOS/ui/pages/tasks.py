from datetime import date

from PySide6.QtCore import QDate
from PySide6.QtWidgets import QCheckBox, QComboBox, QDateEdit, QHBoxLayout, QLineEdit

from ..widgets import Panel, button, label, page_head
from .base import DynamicPage

PRIORITIES = ["High", "Medium", "Low"]
KINDS = ["Assignment", "Lecture", "Revision", "Other"]


class TasksPage(DynamicPage):
    filter_mode = "Pending"

    def build(self, layout):
        layout.addWidget(page_head("Tasks", "Assignments, lectures and chapter revisions. Due dates also appear in the Planner."))

        add = Panel("Add a task")
        row = QHBoxLayout()
        self.title = QLineEdit(placeholderText="What needs doing?")
        self.title.returnPressed.connect(self.add)
        self.has_due = QCheckBox("Due")
        self.due = QDateEdit(QDate.currentDate(), calendarPopup=True)
        self.due.setEnabled(False)
        self.has_due.toggled.connect(self.due.setEnabled)
        self.prio = QComboBox()
        self.prio.addItems(PRIORITIES)
        self.prio.setCurrentText("Medium")
        self.kind = QComboBox()
        self.kind.addItems(KINDS)
        for w in (self.title,):
            row.addWidget(w, 1)
        for w in (self.has_due, self.due, self.prio, self.kind, button("Add", "primary", self.add)):
            row.addWidget(w)
        add.body.addLayout(row)
        layout.addWidget(add)

        lst = Panel()
        head = QHBoxLayout()
        flt = QComboBox()
        flt.addItems(["Pending", "Done", "All"])
        flt.setCurrentText(self.filter_mode)
        flt.currentTextChanged.connect(self._set_filter)
        head.addWidget(label("Show", muted=True))
        head.addWidget(flt)
        head.addStretch(1)
        lst.body.addLayout(head)

        rank = {p: i for i, p in enumerate(PRIORITIES)}
        tasks = sorted(self.db.list("tasks"),
                       key=lambda t: (t.get("done", False), rank.get(t["priority"], 1), t.get("due") or "9999"))
        shown = [t for t in tasks if self.filter_mode == "All"
                 or (self.filter_mode == "Done") == bool(t.get("done"))]
        if not shown:
            lst.body.addWidget(label("Nothing here.", muted=True))
        for t in shown:
            lst.body.addLayout(self._row(t))
        layout.addWidget(lst)

    def _row(self, t):
        row = QHBoxLayout()
        cb = QCheckBox(t["title"])
        cb.setChecked(bool(t.get("done")))
        if t.get("done"):
            cb.setStyleSheet("color:#6c7191;text-decoration:line-through;")
        cb.toggled.connect(lambda v, tid=t["id"]: self.toggle(tid, v))
        row.addWidget(cb, 1)
        row.addWidget(label(t.get("kind", ""), chip="true"))
        if t.get("due"):
            late = t["due"] < date.today().isoformat() and not t.get("done")
            row.addWidget(label(t["due"], chip="bad" if late else "true"))
        row.addWidget(label(t["priority"], chip={"High": "bad", "Medium": "warn"}.get(t["priority"], "true")))
        row.addWidget(button("Delete", "ghost", lambda tid=t["id"]: self.delete(tid), "sm"))
        return row

    def _set_filter(self, mode):
        TasksPage.filter_mode = mode
        self.refresh()

    def add(self):
        title = self.title.text().strip()
        if not title:
            return
        self.db.add("tasks", title=title, done=False, priority=self.prio.currentText(), kind=self.kind.currentText(),
                    due=self.due.date().toString("yyyy-MM-dd") if self.has_due.isChecked() else "")
        self.ctx.data_changed.emit("tasks")
        self.refresh()

    def toggle(self, tid, done):
        self.db.update("tasks", tid, done=done)
        self.ctx.data_changed.emit("tasks")
        self.refresh()

    def delete(self, tid):
        self.db.remove("tasks", tid)
        self.refresh()
