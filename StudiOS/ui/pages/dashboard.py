from datetime import date, datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLineEdit, QVBoxLayout, QWidget

from ...core import stats
from ..widgets import BarChart, Panel, StatCard, button, course_icon, label, page_head
from .base import DynamicPage


class DashboardPage(DynamicPage):
    def build(self, layout):
        db, p = self.db, self.db.profile()
        on = set(p["modules"])
        hour = datetime.now().hour
        greet = "Good morning" if hour < 12 else "Good afternoon" if hour < 17 else "Good evening"
        sub = " · ".join(x for x in [p["exam"], self._countdown(p)] if x) or "Here is your study day."
        layout.addWidget(page_head(f"{greet}, {p['name'] or 'there'}", sub))

        # Row of readouts
        done, total = stats.tasks_done(db)
        quiz = stats.quiz_average(db)
        row = QHBoxLayout()
        row.setSpacing(16)
        for value, cap in [
            (f"{stats.minutes_today(db)}m", "studied today"),
            (f"{total - done}", "tasks pending"),
            (f"{quiz}%" if quiz is not None else "-", "quiz average"),
            (f"{stats.streak(db)}d", "study streak"),
        ]:
            row.addWidget(StatCard(value, cap))
        layout.addLayout(row)

        grid = QGridLayout()
        grid.setSpacing(16)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        cards = []
        if "courses" in on:
            cards.append((self._courses(), True))
        if "planner" in on:
            cards.append((self._plan(), False))
        if "tasks" in on:
            cards.append((self._tasks(), False))
        if "notes" in on:
            cards.append((self._notes(), False))
        if "progress" in on:
            cards.append((self._chart(), False))
        if "assistant" in on:
            cards.append((self._ask(), False))
        r = c = 0
        for card, wide in cards:
            if wide:
                if c:
                    r, c = r + 1, 0
                grid.addWidget(card, r, 0, 1, 2)
                r += 1
            else:
                grid.addWidget(card, r, c)
                c += 1
                if c == 2:
                    r, c = r + 1, 0
        layout.addLayout(grid)

    @staticmethod
    def _countdown(p):
        try:
            days = (date.fromisoformat(p["exam_date"]) - date.today()).days
        except ValueError:
            return ""
        return f"{days} days to exam" if days >= 0 else ""

    def _link(self, panel, text, page):
        panel.body.addWidget(button(text, "link", lambda: self.ctx.go(page)))

    def _courses(self):
        panel = Panel("Courses", button("Manage", "link", lambda: self.ctx.go("courses")))
        courses = self.db.list("courses")
        if not courses:
            panel.body.addWidget(label("No courses yet. Add your first one to get a launcher here.", muted=True))
            return panel
        row = QHBoxLayout()
        row.setSpacing(18)
        for c in courses[:8]:
            col = QVBoxLayout()
            col.setSpacing(4)
            icon = course_icon(self.ctx, c, 52)
            icon.setCursor(Qt.PointingHandCursor)
            icon.mousePressEvent = lambda e, cc=c: self.ctx.go("courses")
            col.addWidget(icon, 0, Qt.AlignHCenter)
            name = label(c["title"][:14], muted=True)
            name.setAlignment(Qt.AlignHCenter)
            col.addWidget(name)
            row.addLayout(col)
        row.addStretch(1)
        panel.body.addLayout(row)
        return panel

    def _plan(self):
        panel = Panel("Today's plan", button("Planner", "link", lambda: self.ctx.go("planner")))
        today = date.today().isoformat()
        blocks = sorted((b for b in self.db.list("blocks") if b["date"] == today), key=lambda b: b["start"])
        if not blocks:
            panel.body.addWidget(label("Nothing scheduled today.", muted=True))
        for b in blocks[:5]:
            panel.body.addWidget(label(f"{b['start']}   {b['subject']}  ({b['minutes']} min)"))
        return panel

    def _tasks(self):
        panel = Panel("Priority tasks", button("Tasks", "link", lambda: self.ctx.go("tasks")))
        rank = {"High": 0, "Medium": 1, "Low": 2}
        pending = sorted((t for t in self.db.list("tasks") if not t.get("done")),
                         key=lambda t: (rank.get(t.get("priority"), 1), t.get("due") or "9999"))
        if not pending:
            panel.body.addWidget(label("All clear.", muted=True))
        for t in pending[:5]:
            row = QHBoxLayout()
            row.addWidget(label(t["title"]), 1)
            row.addWidget(label(t.get("priority", "Medium"),
                                chip={"High": "bad", "Medium": "warn"}.get(t.get("priority"), "true")))
            panel.body.addLayout(row)
        return panel

    def _notes(self):
        panel = Panel("Recent notes", button("Notes", "link", lambda: self.ctx.go("notes")))
        notes = sorted(self.db.list("notes"), key=lambda n: n["updated"], reverse=True)
        if not notes:
            panel.body.addWidget(label("No notes yet.", muted=True))
        for n in notes[:4]:
            panel.body.addWidget(button(n["title"] or "Untitled", "link",
                                        lambda nid=n["id"]: self.ctx.go("notes", note_id=nid)))
        return panel

    def _chart(self):
        panel = Panel("Last 7 days (minutes)", button("Progress", "link", lambda: self.ctx.go("progress")))
        panel.body.addWidget(BarChart(stats.last_days(self.db)))
        return panel

    def _ask(self):
        panel = Panel("Ask the assistant")
        s = self.ctx.status
        panel.body.addWidget(label(
            f"Model ready: {s['active']}" if s.get("model_ready") else "AI is offline. Open Settings to connect Ollama.",
            muted=True))
        edit = QLineEdit()
        edit.setPlaceholderText("Type a doubt and press Enter")
        edit.returnPressed.connect(lambda: self.ctx.go("assistant", prefill=edit.text(), send=True))
        panel.body.addWidget(edit)
        return panel
