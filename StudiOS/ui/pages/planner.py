from datetime import date, datetime, timedelta

from PySide6.QtCore import QDate, QTime, QTimer
from PySide6.QtWidgets import (
    QComboBox, QDateEdit, QDialog, QDialogButtonBox, QFormLayout, QGridLayout, QHBoxLayout, QListWidget,
    QListWidgetItem, QLineEdit, QSpinBox, QTimeEdit, QVBoxLayout,
)
from PySide6.QtCore import Qt

from ... import config
from ..widgets import Panel, button, confirm, label, page_head
from .base import DynamicPage


class BlockDialog(QDialog):
    def __init__(self, parent, day: date, subjects):
        super().__init__(parent)
        self.setWindowTitle("Add study block")
        self.date = QDateEdit(QDate(day.year, day.month, day.day), calendarPopup=True)
        self.start = QTimeEdit(QTime(18, 0))
        self.minutes = QSpinBox(minimum=10, maximum=480, singleStep=5, value=45, suffix=" min")
        self.subject = QComboBox(editable=True)
        self.subject.addItems(subjects)
        form = QFormLayout()
        form.addRow("Date", self.date)
        form.addRow("Start", self.start)
        form.addRow("Length", self.minutes)
        form.addRow("Subject", self.subject)
        bb = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        lay = QVBoxLayout(self)
        lay.addLayout(form)
        lay.addWidget(bb)

    def values(self):
        return dict(date=self.date.date().toString("yyyy-MM-dd"), start=self.start.time().toString("HH:mm"),
                    minutes=self.minutes.value(), subject=self.subject.currentText().strip() or "Study")


class PlannerPage(DynamicPage):
    week_offset = 0

    def setup(self):
        super().setup()
        self.tick = QTimer(self, interval=1000)
        self.tick.timeout.connect(self._tick)
        self.clock = None

    def subjects(self):
        found = {c.get("subject") for c in self.db.list("courses")} | {n.get("subject") for n in self.db.list("notes")}
        return sorted(s for s in found if s) or config.SUBJECTS

    def build(self, layout):
        monday = date.today() - timedelta(days=date.today().weekday()) + timedelta(weeks=self.week_offset)
        layout.addWidget(page_head(
            "Planner", self._countdown() or "Block out your week and time each session.",
            button("AI suggest week", None, self.suggest, tip="Asks the local model for a draft plan"),
            button("Add block", "primary", lambda: self.add(monday))))
        layout.addWidget(self._timer_panel())

        nav = QHBoxLayout()
        nav.addWidget(button("‹", "ghost", lambda: self._shift(-1), "sm"))
        nav.addWidget(button("This week", "ghost", lambda: self._shift(0), "sm"))
        nav.addWidget(button("›", "ghost", lambda: self._shift(1), "sm"))
        nav.addWidget(label(f"{monday.strftime('%d %b')} - {(monday + timedelta(days=6)).strftime('%d %b %Y')}", muted=True))
        nav.addStretch(1)
        layout.addLayout(nav)

        blocks, tasks = self.db.list("blocks"), [t for t in self.db.list("tasks") if t.get("due") and not t.get("done")]
        grid = QGridLayout()
        grid.setSpacing(10)
        for i in range(7):
            d = monday + timedelta(days=i)
            iso = d.isoformat()
            col = Panel()
            col.body.setSpacing(6)
            col.body.addWidget(label(d.strftime("%a %d"), "h2" if d == date.today() else None, muted=d != date.today()))
            for b in sorted((b for b in blocks if b["date"] == iso), key=lambda b: b["start"]):
                col.body.addWidget(label(f"{b['start']}  {b['subject']}\n{b['minutes']} min", wrap=True))
                row = QHBoxLayout()
                row.addWidget(button("Start", None, lambda bb=b: self.start(bb), "sm"))
                row.addWidget(button("×", "ghost", lambda bb=b: self.remove(bb), "sm"))
                col.body.addLayout(row)
            for t in (t for t in tasks if t["due"] == iso):
                col.body.addWidget(label(f"Due: {t['title'][:22]}", chip="warn"))
            col.body.addStretch(1)
            grid.addWidget(col, 0, i)
            grid.setColumnStretch(i, 1)
        layout.addLayout(grid)
        self.tick.start()

    def _countdown(self):
        try:
            d = (date.fromisoformat(self.db.profile()["exam_date"]) - date.today()).days
            return f"{d} days until your exam" if d >= 0 else ""
        except ValueError:
            return ""

    def _shift(self, n):
        PlannerPage.week_offset = 0 if n == 0 else PlannerPage.week_offset + n
        self.refresh()

    # ---- timer ----
    def _timer_panel(self):
        t = self.ctx.timer
        p = Panel("Study timer")
        row = QHBoxLayout()
        self.timer_subject = QComboBox(editable=True)
        self.timer_subject.addItems(self.subjects())
        if t.subject:
            self.timer_subject.setCurrentText(t.subject)
        self.timer_subject.setEnabled(t.state == "idle")
        self.clock = label(self._fmt(t.elapsed()), "statValue")
        row.addWidget(self.clock)
        row.addSpacing(12)
        row.addWidget(self.timer_subject, 1)
        if t.state == "running":
            row.addWidget(button("Pause", None, self._pause))
        else:
            row.addWidget(button("Resume" if t.state == "paused" else "Start", "primary", self._go))
        row.addWidget(button("Stop and log", None, self._stop))
        p.body.addLayout(row)
        return p

    @staticmethod
    def _fmt(s):
        return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"

    def _tick(self):
        if self.clock is not None:
            try:
                self.clock.setText(self._fmt(self.ctx.timer.elapsed()))
            except RuntimeError:  # label was rebuilt
                self.clock = None

    def _go(self):
        self.ctx.timer.start(self.timer_subject.currentText().strip() or "Study")
        self.refresh()

    def _pause(self):
        self.ctx.timer.pause()
        self.refresh()

    def _stop(self):
        subject, mins = self.ctx.timer.stop()
        if mins:
            self.db.add("sessions", date=date.today().isoformat(), minutes=mins, subject=subject)
            self.ctx.data_changed.emit("sessions")
            self.ctx.toast.emit(f"Logged {mins} min of {subject}")
        self.refresh()

    def start(self, b):
        if self.ctx.timer.state == "idle":
            self.ctx.timer.start(b["subject"])
        self.refresh()

    # ---- blocks ----
    def add(self, monday):
        day = date.today() if monday <= date.today() <= monday + timedelta(days=6) else monday
        d = BlockDialog(self, day, self.subjects())
        if d.exec():
            self.db.add("blocks", **d.values())
            self.refresh()

    def remove(self, b):
        self.db.remove("blocks", b["id"])
        self.refresh()

    # ---- AI suggestion (optional) ----
    def suggest(self):
        if not self.ctx.status.get("model_ready"):
            self.ctx.toast.emit("AI is offline. Open Settings to connect Ollama.")
            return
        p = self.db.profile()
        msg = [{"role": "system", "content": "You are a study planner. Reply with valid JSON only."},
               {"role": "user", "content":
                   f"Today is {date.today().isoformat()}. Exam: {p['exam'] or 'not set'}, "
                   f"exam date: {p['exam_date'] or 'not set'}. Subjects: {', '.join(self.subjects())}.\n"
                   'Plan 2 study blocks per day for the next 7 days. Return JSON: {"blocks":[{"date":"YYYY-MM-DD",'
                   '"start":"HH:MM","minutes":45,"subject":"..."}]}. Use only the listed subjects.'}]
        self.ctx.toast.emit("Asking the model for a plan...")
        self.ctx.run(lambda w: self.ctx.ollama.chat_json(msg), on_done=self._review, on_fail=self.ctx.toast.emit)

    def _review(self, obj):
        items = []
        for b in obj.get("blocks", []) if isinstance(obj, dict) else []:
            try:
                date.fromisoformat(b["date"])
                datetime.strptime(b["start"], "%H:%M")
                items.append(dict(date=b["date"], start=b["start"], minutes=int(b.get("minutes", 45)),
                                  subject=str(b.get("subject", "Study"))))
            except (KeyError, ValueError, TypeError):
                continue
        if not items:
            self.ctx.toast.emit("The model's plan could not be read. Try again.")
            return
        dlg = QDialog(self)
        dlg.setWindowTitle("Suggested plan")
        dlg.setMinimumWidth(420)
        lst = QListWidget()
        for b in items:
            it = QListWidgetItem(f"{b['date']}  {b['start']}  {b['subject']}  ({b['minutes']} min)")
            it.setFlags(it.flags() | Qt.ItemIsUserCheckable)
            it.setCheckState(Qt.Checked)
            it.setData(Qt.UserRole, b)
            lst.addItem(it)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.button(QDialogButtonBox.Ok).setText("Add selected")
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        lay = QVBoxLayout(dlg)
        lay.addWidget(label("Untick anything you do not want.", muted=True))
        lay.addWidget(lst)
        lay.addWidget(bb)
        if dlg.exec():
            for i in range(lst.count()):
                if lst.item(i).checkState() == Qt.Checked:
                    self.db.add("blocks", **lst.item(i).data(Qt.UserRole))
            self.refresh()
