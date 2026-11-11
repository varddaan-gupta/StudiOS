from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup, QComboBox, QFrame, QHBoxLayout, QLineEdit, QPlainTextEdit, QRadioButton, QScrollArea,
    QSpinBox, QStackedWidget, QVBoxLayout, QWidget,
)

from ...core import quiz as Q
from ..widgets import Panel, button, clear_layout, confirm, label, page_head
from .base import Page


class ItemEditor(QFrame):
    """One editable question or flashcard in the draft."""

    def __init__(self, kind, item, on_remove):
        super().__init__()
        self.kind = kind
        self.setObjectName("quizOption")
        lay = QVBoxLayout(self)
        top = QHBoxLayout()
        if kind == Q.MCQ:
            self.q = QLineEdit(item["q"])
            top.addWidget(self.q, 1)
            top.addWidget(button("Remove", "ghost", lambda: on_remove(self), "sm"))
            lay.addLayout(top)
            self.group = QButtonGroup(self)
            self.opts = []
            for i in range(4):
                row = QHBoxLayout()
                rb = QRadioButton()
                self.group.addButton(rb, i)
                ed = QLineEdit(item["options"][i] if i < len(item["options"]) else "")
                ed.setPlaceholderText(f"Option {'ABCD'[i]}")
                self.opts.append(ed)
                row.addWidget(rb)
                row.addWidget(ed, 1)
                lay.addLayout(row)
            self.group.button(item["answer"]).setChecked(True)
            self.expl = QLineEdit(item.get("explanation", ""))
            self.expl.setPlaceholderText("Why this answer is right (optional)")
            lay.addWidget(self.expl)
        else:
            self.front = QLineEdit(item["front"])
            self.back = QPlainTextEdit(item["back"])
            self.back.setFixedHeight(60)
            top.addWidget(self.front, 1)
            top.addWidget(button("Remove", "ghost", lambda: on_remove(self), "sm"))
            lay.addLayout(top)
            lay.addWidget(self.back)

    def value(self):
        if self.kind == Q.MCQ:
            opts = [(i, o.text().strip()) for i, o in enumerate(self.opts) if o.text().strip()]
            ans = next((n for n, (i, _) in enumerate(opts) if i == self.group.checkedId()), None)
            if not self.q.text().strip() or len(opts) < 2 or ans is None:
                return None
            return {"q": self.q.text().strip(), "options": [o for _, o in opts], "answer": ans,
                    "explanation": self.expl.text().strip()}
        f, b = self.front.text().strip(), self.back.toPlainText().strip()
        return {"front": f, "back": b} if f and b else None


class Player(QWidget):
    """Runs one quiz or flashcard set and reports the score."""

    def __init__(self, quiz_set, on_finish, on_exit):
        super().__init__()
        self.set, self.on_finish, self.on_exit = quiz_set, on_finish, on_exit
        self.items, self.i, self.score = quiz_set["items"], 0, 0
        self.lay = QVBoxLayout(self)
        self.show_item()

    def show_item(self):
        clear_layout(self.lay)
        if self.i >= len(self.items):
            return self.finish()
        it = self.items[self.i]
        self.lay.addWidget(label(f"{self.i + 1} of {len(self.items)}", muted=True))
        if self.set["kind"] == Q.MCQ:
            self.lay.addWidget(label(it["q"], "h2", wrap=True))
            self.btns = []
            for n, o in enumerate(it["options"]):
                b = button(f"{'ABCD'[n]}.  {o}", None, lambda k=n: self.answer(k))
                b.setStyleSheet("text-align:left;padding:10px 14px;")
                self.btns.append(b)
                self.lay.addWidget(b)
            self.note = label("", muted=True, wrap=True)
            self.next = button("Next", "primary", self.advance)
            self.next.hide()
            self.lay.addWidget(self.note)
            self.lay.addWidget(self.next, 0, Qt.AlignLeft)
        else:
            self.flipped = False
            self.card = QFrame()
            self.card.setObjectName("flashCard")
            self.card.setMinimumHeight(180)
            cl = QVBoxLayout(self.card)
            self.face = label(it["front"], "h2", wrap=True)
            self.face.setAlignment(Qt.AlignCenter)
            cl.addWidget(self.face)
            self.lay.addWidget(self.card)
            self.flip_btn = button("Show answer", None, self.flip)
            self.lay.addWidget(self.flip_btn, 0, Qt.AlignLeft)
            self.grade = QWidget()
            g = QHBoxLayout(self.grade)
            g.setContentsMargins(0, 0, 0, 0)
            g.addWidget(button("Knew it", "primary", lambda: self.mark(True)))
            g.addWidget(button("Again", None, lambda: self.mark(False)))
            g.addStretch(1)
            self.grade.hide()
            self.lay.addWidget(self.grade)
        self.lay.addStretch(1)
        self.lay.addWidget(button("Quit", "ghost", self.on_exit, "sm"), 0, Qt.AlignLeft)

    def answer(self, k):
        it = self.items[self.i]
        for n, b in enumerate(self.btns):
            b.setEnabled(False)
            if n == it["answer"]:
                b.setProperty("state", "right")
            elif n == k:
                b.setProperty("state", "wrong")
            b.style().unpolish(b)
            b.style().polish(b)
        self.score += k == it["answer"]
        self.note.setText(("Correct. " if k == it["answer"] else "Not quite. ") + it.get("explanation", ""))
        self.next.show()

    def flip(self):
        self.flipped = True
        self.face.setText(self.items[self.i]["back"])
        self.flip_btn.hide()
        self.grade.show()

    def mark(self, knew):
        self.score += knew
        self.advance()

    def advance(self):
        self.i += 1
        self.show_item()

    def finish(self):
        total = len(self.items)
        self.on_finish(self.score, total)
        pct = round(self.score / total * 100)
        self.lay.addWidget(label(f"{self.score} / {total}", "statValue"))
        self.lay.addWidget(label(f"{pct}% " + ("Strong. Keep it up." if pct >= 70 else "Review the notes and try again."),
                                 muted=True))
        self.lay.addWidget(button("Back to sets", "primary", self.on_exit), 0, Qt.AlignLeft)
        self.lay.addStretch(1)


class RevisionPage(Page):
    scroll = True

    def setup(self):
        self.draft = None  # {"kind": ..., "editors": [...]}
        self.worker = None
        self.stack = QStackedWidget()
        self.root.addWidget(self.stack)
        self.home = QWidget()
        self.hl = QVBoxLayout(self.home)
        self.hl.setContentsMargins(0, 0, 0, 0)
        self.hl.setSpacing(14)
        self.stack.addWidget(self.home)
        self.player_holder = QWidget()
        self.pl = QVBoxLayout(self.player_holder)
        self.stack.addWidget(self.player_holder)

        self.hl.addWidget(page_head("Revision", "Turn notes into practice. Edit anything the AI gets wrong."))
        gen = Panel("Generate questions")
        self.source = QComboBox()
        self.text = QPlainTextEdit(placeholderText="Or paste text here")
        self.text.setFixedHeight(100)
        self.kind = QComboBox()
        self.kind.addItem("Multiple choice", Q.MCQ)
        self.kind.addItem("Flashcards", Q.FLASH)
        self.count = QSpinBox(minimum=3, maximum=12, value=5)
        self.gen_btn = button("Generate", "primary", self.generate)
        self.gen_status = label("", muted=True, wrap=True)
        row = QHBoxLayout()
        for w in (self.source, self.kind, self.count, self.gen_btn):
            row.addWidget(w)
        row.addStretch(1)
        gen.body.addLayout(row)
        gen.body.addWidget(self.text)
        gen.body.addWidget(self.gen_status)
        self.hl.addWidget(gen)

        self.draft_panel = Panel("Review your draft")
        self.draft_title = QLineEdit(placeholderText="Name this set")
        self.draft_list = QVBoxLayout()
        self.draft_panel.body.addWidget(self.draft_title)
        self.draft_panel.body.addLayout(self.draft_list)
        self.draft_panel.body.addWidget(button("Save set", "primary", self.save_draft), 0, Qt.AlignLeft)
        self.draft_panel.hide()
        self.hl.addWidget(self.draft_panel)

        self.sets_panel = Panel("Your sets")
        self.sets_box = QVBoxLayout()
        self.sets_panel.body.addLayout(self.sets_box)
        self.hl.addWidget(self.sets_panel)
        self.hl.addStretch(1)

    def refresh(self):
        self.stack.setCurrentIndex(0)
        want = self.ctx.handoff.pop("note_id", None)
        self.source.clear()
        self.source.addItem("Pasted text below", "")
        for n in self.db.list("notes"):
            self.source.addItem(f"Note: {n['title'] or 'Untitled'}", n["id"])
        if want:
            self.source.setCurrentIndex(max(self.source.findData(want), 0))
        self._sets()

    def _sets(self):
        clear_layout(self.sets_box)
        sets = self.db.list("quizzes")
        if not sets:
            self.sets_box.addWidget(label("No sets yet.", muted=True))
        for s in sets:
            res = [r for r in self.db.list("results") if r["quiz_id"] == s["id"]]
            best = max((round(r["score"] / r["total"] * 100) for r in res if r["total"]), default=None)
            row = QHBoxLayout()
            row.addWidget(label(s["title"]), 1)
            row.addWidget(label("Cards" if s["kind"] == Q.FLASH else "MCQ", chip="true"))
            row.addWidget(label(f"{len(s['items'])} items", muted=True))
            row.addWidget(label(f"best {best}%" if best is not None else "not taken", chip="accent" if best else "true"))
            row.addWidget(button("Practice", "primary", lambda ss=s: self.practice(ss), "sm"))
            row.addWidget(button("Delete", "ghost", lambda ss=s: self.delete(ss), "sm"))
            self.sets_box.addLayout(row)

    # ---- generation ----
    def generate(self):
        note = self.db.get("notes", self.source.currentData()) if self.source.currentData() else None
        material = (note["body"] if note else self.text.toPlainText()).strip()
        if len(material) < 40:
            self.gen_status.setText("Add a longer note or paste at least a few sentences.")
            return
        if not self.ctx.status.get("model_ready"):
            self.gen_status.setText("AI is offline. Open Settings to connect Ollama.")
            return
        kind, n = self.kind.currentData(), self.count.value()
        self.gen_btn.setEnabled(False)
        self.gen_status.setText("Writing questions with your local model. This can take a minute...")
        title = note["title"] if note else "Pasted text"
        self.ctx.run(lambda w: Q.normalize(kind, self.ctx.ollama.chat_json(Q.build_messages(kind, n, material))),
                     on_done=lambda items: self._drafted(kind, title, items), on_fail=self._gen_failed)

    def _gen_failed(self, msg):
        self.gen_btn.setEnabled(True)
        self.gen_status.setText(msg)

    def _drafted(self, kind, title, items):
        self.gen_btn.setEnabled(True)
        if not items:
            self.gen_status.setText("The model did not return usable questions. Try again, or use a clearer note.")
            return
        self.gen_status.setText(f"{len(items)} items ready. Fix anything wrong, then save.")
        clear_layout(self.draft_list)
        self.draft = {"kind": kind, "editors": []}
        self.draft_title.setText(f"{title} - {'cards' if kind == Q.FLASH else 'quiz'}")
        for it in items:
            ed = ItemEditor(kind, it, self._remove_editor)
            self.draft["editors"].append(ed)
            self.draft_list.addWidget(ed)
        self.draft_panel.show()

    def _remove_editor(self, ed):
        self.draft["editors"].remove(ed)
        ed.deleteLater()

    def save_draft(self):
        items = [v for ed in self.draft["editors"] if (v := ed.value())]
        if not items:
            self.gen_status.setText("Nothing valid to save. Each question needs 2+ options and a chosen answer.")
            return
        self.db.add("quizzes", title=self.draft_title.text().strip() or "Untitled set",
                    kind=self.draft["kind"], items=items)
        self.draft = None
        clear_layout(self.draft_list)
        self.draft_panel.hide()
        self.gen_status.setText("Saved.")
        self._sets()

    # ---- practice ----
    def practice(self, s):
        clear_layout(self.pl)
        self.pl.addWidget(label(s["title"], "h1"))
        self.pl.addWidget(Player(s, lambda sc, tot: self._record(s, sc, tot), self.refresh))
        self.stack.setCurrentIndex(1)

    def _record(self, s, score, total):
        self.db.add("results", quiz_id=s["id"], kind=s["kind"], score=score, total=total,
                    date=date.today().isoformat())
        self.ctx.data_changed.emit("results")

    def delete(self, s):
        if confirm(self, f"Delete \"{s['title']}\"?"):
            self.db.remove("quizzes", s["id"])
            self._sets()
