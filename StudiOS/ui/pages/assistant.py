import html
import re

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox, QHBoxLayout, QLineEdit, QListWidget, QListWidgetItem, QTextBrowser, QVBoxLayout,
)

from ...core.context import build_system_prompt
from ..theme import C
from ..widgets import Panel, button, label, page_head
from .base import Page


def md_to_html(text):
    """Tiny markdown subset: code, bold, bullets, line breaks."""
    t = html.escape(text)
    t = re.sub(r"```(?:\w+)?\n?(.*?)```", r"<pre>\1</pre>", t, flags=re.S)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?m)^\s*[-*] ", "&bull; ", t)
    return t.replace("\n", "<br>")


class AssistantPage(Page):
    scroll = False

    def setup(self):
        self.history, self.worker = [], None
        self.root.addWidget(page_head("Assistant", "Answers come from your active course and the notes you tick."))
        row = QHBoxLayout()
        row.setSpacing(16)
        self.root.addLayout(row, 1)

        # context column
        side = Panel("Context")
        side.setFixedWidth(280)
        self.course = QComboBox()
        self.subject = QLineEdit(placeholderText="Subject (optional)")
        self.notes = QListWidget()
        side.body.addWidget(label("Course", muted=True))
        side.body.addWidget(self.course)
        side.body.addWidget(self.subject)
        side.body.addWidget(label("Notes to rely on", muted=True))
        side.body.addWidget(self.notes, 1)
        side.body.addWidget(button("New chat", "ghost", self.clear))
        row.addWidget(side)

        # chat column
        chat = Panel()
        self.banner = label("", chip="bad", wrap=True)
        self.view = QTextBrowser()
        self.view.document().setDefaultStyleSheet(
            f"pre{{background:{C['ground']};}} code{{color:{C['accent2']};}}")
        self.input = QLineEdit(placeholderText="Ask a doubt, request a summary, or a formula breakdown")
        self.input.returnPressed.connect(self.send)
        self.send_btn = button("Send", "primary", self.send)
        self.stop_btn = button("Stop", None, self.stop)
        self.stop_btn.hide()
        bar = QHBoxLayout()
        bar.addWidget(self.input, 1)
        bar.addWidget(self.send_btn)
        bar.addWidget(self.stop_btn)
        chat.body.addWidget(self.banner)
        chat.body.addWidget(self.view, 1)
        chat.body.addLayout(bar)
        row.addWidget(chat, 1)
        self.render()

    def refresh(self):
        keep = {self.notes.item(i).data(Qt.UserRole) for i in range(self.notes.count())
                if self.notes.item(i).checkState() == Qt.Checked}
        h = self.ctx.handoff
        keep |= set(h.pop("note_ids", []))
        cur_course = h.pop("course_id", None) or self.course.currentData()
        self.course.clear()
        self.course.addItem("No course", "")
        for c in self.db.list("courses"):
            self.course.addItem(c["title"], c["id"])
        self.course.setCurrentIndex(max(self.course.findData(cur_course), 0))
        self.notes.clear()
        for n in self.db.list("notes"):
            it = QListWidgetItem(n["title"] or "Untitled")
            it.setFlags(it.flags() | Qt.ItemIsUserCheckable)
            it.setCheckState(Qt.Checked if n["id"] in keep else Qt.Unchecked)
            it.setData(Qt.UserRole, n["id"])
            self.notes.addItem(it)
        s = self.ctx.status
        self.banner.setVisible(not s.get("model_ready"))
        self.banner.setText(s.get("error") or "No model installed. Open Settings to download one.")
        if (pre := h.pop("prefill", None)):
            self.input.setText(pre)
            if h.pop("send", False):
                self.send()

    def _context(self):
        course = self.db.get("courses", self.course.currentData()) if self.course.currentData() else None
        notes = [self.db.get("notes", self.notes.item(i).data(Qt.UserRole)) for i in range(self.notes.count())
                 if self.notes.item(i).checkState() == Qt.Checked]
        return build_system_prompt(self.db.profile()["exam"], course, self.subject.text().strip() or None,
                                   [n for n in notes if n])

    def render(self):
        if not self.history:
            self.view.setHtml(f"<p style='color:{C['muted']}'>Ask anything about what you are studying. "
                              "Tick notes on the left and the answer will stay grounded in them.</p>")
            return
        parts = []
        for m in self.history:
            you = m["role"] == "user"
            bg, who = (C["panel2"], "You") if you else (C["ground"], "StudiOS")
            colour = C["bad"] if m.get("error") else C["text"]
            parts.append(
                f"<table width='100%' cellpadding='10' cellspacing='0' style='margin-bottom:8px'><tr>"
                f"<td bgcolor='{bg}'><span style='color:{C['accent']}'><b>{who}</b></span><br>"
                f"<span style='color:{colour}'>{md_to_html(m['content']) or '...'}</span></td></tr></table>")
        self.view.setHtml("".join(parts))
        self.view.verticalScrollBar().setValue(self.view.verticalScrollBar().maximum())

    def send(self):
        text = self.input.text().strip()
        if not text or self.worker:
            return
        self.input.clear()
        self.history += [{"role": "user", "content": text}, {"role": "assistant", "content": ""}]
        self.render()
        msgs = [{"role": "system", "content": self._context()},
                *[{"role": m["role"], "content": m["content"]} for m in self.history[:-1][-10:]]]
        self.send_btn.hide()
        self.stop_btn.show()
        self.worker = self.ctx.run(
            lambda w: self.ctx.ollama.chat_stream(msgs, w.token.emit, lambda: w.stopped),
            on_token=self._token, on_done=lambda _r: self._finish(), on_fail=self._fail)

    def _token(self, t):
        self.history[-1]["content"] += t
        self.render()

    def _fail(self, msg):
        self.history[-1].update(content=msg, error=True)
        self._finish()

    def _finish(self):
        self.worker = None
        self.send_btn.show()
        self.stop_btn.hide()
        self.render()

    def stop(self):
        if self.worker:
            self.worker.stop()

    def clear(self):
        self.stop()
        self.history = []
        self.render()
