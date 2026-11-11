from PySide6.QtWidgets import QHBoxLayout

from ...core import stats
from ..widgets import BarChart, Panel, StatCard, label, meter, page_head
from .base import DynamicPage


class ProgressPage(DynamicPage):
    def build(self, layout):
        db = self.db
        layout.addWidget(page_head("Progress", "Plain numbers from what you actually did. No predictions."))
        done, total = stats.tasks_done(db)
        quiz = stats.quiz_average(db)
        week = stats.last_days(db, 7)
        row = QHBoxLayout()
        row.setSpacing(16)
        for v, cap in [(f"{round(done / total * 100) if total else 0}%", f"tasks done ({done} of {total})"),
                       (f"{quiz}%" if quiz is not None else "-", "quiz average"),
                       (f"{sum(m for _, m in week)}m", "studied this week"),
                       (f"{stats.streak(db)}d", "current streak")]:
            row.addWidget(StatCard(v, cap))
        layout.addLayout(row)

        chart = Panel("Study minutes, last 7 days")
        chart.body.addWidget(BarChart(week))
        layout.addWidget(chart)

        courses = Panel("Course topics")
        cs = db.list("courses")
        if not cs:
            courses.body.addWidget(label("Add courses to track topic progress.", muted=True))
        for c in cs:
            courses.body.addWidget(label(f"{c['title']}  -  {c.get('progress', 0)}%"))
            courses.body.addWidget(meter(c.get("progress", 0)))
        layout.addWidget(courses)

        res = Panel("Recent quiz scores")
        results = sorted(db.list("results"), key=lambda r: r["created"], reverse=True)[:8]
        if not results:
            res.body.addWidget(label("No quizzes taken yet. Make one from a note in Revision.", muted=True))
        for r in results:
            q = db.get("quizzes", r["quiz_id"])
            pct = round(r["score"] / r["total"] * 100) if r["total"] else 0
            line = QHBoxLayout()
            line.addWidget(label(q["title"] if q else "Deleted set"), 1)
            line.addWidget(label(f"{r['score']}/{r['total']}", "mono"))
            line.addWidget(label(f"{pct}%", chip="ok" if pct >= 70 else "warn" if pct >= 40 else "bad"))
            res.body.addLayout(line)
        layout.addWidget(res)
