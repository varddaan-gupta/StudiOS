"""Reusable building blocks used by every page."""
from PySide6.QtCore import Qt, QByteArray, QRectF, QPointF, QSize
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPen, QPixmap, QBrush
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget, QProgressBar,
)

from .theme import C, MONO

# ---------- icons (24x24 stroke paths) ----------
ICON_PATHS = {
    "dashboard": "M3 11l9-8 9 8v9a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z",
    "courses": "M4 4h7v7H4zM13 4h7v7h-7zM4 13h7v7H4zM13 13h7v7h-7z",
    "notes": "M6 3h9l4 4v14H6zM14 3v5h5M9 12h7M9 16h7",
    "assistant": "M4 5h16v11H9l-5 4z",
    "planner": "M4 6h16v14H4zM4 10h16M8 3v4M16 3v4",
    "revision": "M4 8h12v10H4zM8 5h12v10",
    "tasks": "M4 12l5 5L20 6",
    "progress": "M5 20V10M12 20V4M19 20v-7",
    "settings": "M4 7h10M18 7h2M4 17h2M10 17h10M14 5v4M6 15v4",
}


def svg_icon(name, color=None, size=24):
    color = color or C["muted"]
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" '
           f'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="{ICON_PATHS[name]}"/></svg>')
    r = QSvgRenderer(QByteArray(svg.encode()))
    pm = QPixmap(size * 2, size * 2)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    r.render(p)
    p.end()
    return QIcon(pm)


def dock_icon(name):
    ic = QIcon()
    ic.addPixmap(svg_icon(name, C["muted"]).pixmap(48, 48), QIcon.Normal, QIcon.Off)
    ic.addPixmap(svg_icon(name, C["accent"]).pixmap(48, 48), QIcon.Normal, QIcon.On)
    return ic


# ---------- small helpers ----------
def clear_layout(layout):
    while layout.count():
        item = layout.takeAt(0)
        if item.widget():
            item.widget().deleteLater()
        elif item.layout():
            clear_layout(item.layout())


def label(text="", name=None, muted=False, wrap=False, chip=None):
    lb = QLabel(text)
    if name:
        lb.setObjectName(name)
    if muted:
        lb.setProperty("muted", True)
    if chip:
        lb.setProperty("chip", chip)
        lb.setFixedHeight(22)
        lb.setAlignment(Qt.AlignCenter)
    lb.setWordWrap(wrap)
    return lb


def button(text, variant=None, cb=None, size=None, tip=None):
    b = QPushButton(text)
    if variant:
        b.setProperty("variant", variant)
    if size:
        b.setProperty("size", size)
    if cb:
        b.clicked.connect(lambda _=False: cb())
    if tip:
        b.setToolTip(tip)
    b.setCursor(Qt.PointingHandCursor)
    return b


def field(text, widget):
    box = QWidget()
    lay = QVBoxLayout(box)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(4)
    lay.addWidget(label(text, muted=True))
    lay.addWidget(widget)
    return box


def hbox(*items, spacing=8, stretch_end=False):
    w = QWidget()
    lay = QHBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(spacing)
    for it in items:
        lay.addWidget(it)
    if stretch_end:
        lay.addStretch(1)
    return w


def page_head(title, sub=None, *actions):
    w = QWidget()
    lay = QHBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 14)
    col = QVBoxLayout()
    col.setSpacing(2)
    col.addWidget(label(title, "h1"))
    if sub:
        col.addWidget(label(sub, muted=True, wrap=True))
    lay.addLayout(col, 1)
    for a in actions:
        lay.addWidget(a, 0, Qt.AlignBottom)
    return w


def confirm(parent, text, yes="Delete"):
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Warning)
    box.setText(text)
    ok = box.addButton(yes, QMessageBox.AcceptRole)
    box.addButton("Cancel", QMessageBox.RejectRole)
    box.exec()
    return box.clickedButton() is ok


def course_icon(ctx, course, size=44):
    lb = QLabel((course.get("title") or "?")[:1].upper())
    lb.setObjectName("courseIcon")
    lb.setFixedSize(size, size)
    lb.setAlignment(Qt.AlignCenter)
    ctx.favicon(course.get("url", ""), lb, size)
    return lb


def meter(value):
    bar = QProgressBar()
    bar.setRange(0, 100)
    bar.setValue(int(value))
    bar.setTextVisible(False)
    return bar


# ---------- custom-painted widgets ----------
class Panel(QFrame):
    """Card with small accent ticks in two corners. Add content to self.body."""

    def __init__(self, title=None, action=None):
        super().__init__()
        self.setAttribute(Qt.WA_StyledBackground, False)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 16, 18, 16)
        outer.setSpacing(10)
        if title or action:
            head = QHBoxLayout()
            if title:
                head.addWidget(label(title, "h2"))
            head.addStretch(1)
            if action:
                head.addWidget(action)
            outer.addLayout(head)
        self.body = QVBoxLayout()
        self.body.setSpacing(8)
        outer.addLayout(self.body, 1)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(.5, .5, -.5, -.5)
        p.setBrush(QColor(C["panel"]))
        p.setPen(QPen(QColor(C["line"]), 1))
        p.drawRoundedRect(r, 10, 10)
        p.setPen(QPen(QColor(C["accent"]), 1.6))
        p.setBrush(Qt.NoBrush)
        L = 10
        p.drawLine(QPointF(r.left() + 2, r.top() + L), QPointF(r.left() + 2, r.top() + 4))
        p.drawLine(QPointF(r.left() + 4, r.top() + 2), QPointF(r.left() + L, r.top() + 2))
        p.drawLine(QPointF(r.right() - 2, r.bottom() - L), QPointF(r.right() - 2, r.bottom() - 4))
        p.drawLine(QPointF(r.right() - 4, r.bottom() - 2), QPointF(r.right() - L, r.bottom() - 2))


class StatCard(Panel):
    def __init__(self, value, caption):
        super().__init__()
        self.body.setSpacing(0)
        self.value = label(str(value), "statValue")
        self.body.addWidget(self.value)
        self.body.addWidget(label(caption, muted=True))


class BarChart(QWidget):
    def __init__(self, data=(), unit="min"):
        super().__init__()
        self.data, self.unit = list(data), unit
        self.setMinimumHeight(130)

    def set_data(self, data):
        self.data = list(data)
        self.update()

    def paintEvent(self, _):
        if not self.data:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        base, top = h - 20, 16
        peak = max(max(v for _, v in self.data), 1)
        slot = w / len(self.data)
        bw = min(34, slot * .55)
        small = QFont("Segoe UI", 8)
        mono = QFont(MONO, 8)
        for i, (lab, v) in enumerate(self.data):
            x = i * slot + (slot - bw) / 2
            bh = max(3, (base - top) * v / peak) if v else 3
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(C["accent"] if v else C["line"]))
            p.drawRoundedRect(QRectF(x, base - bh, bw, bh), 3, 3)
            p.setPen(QColor(C["muted"]))
            p.setFont(small)
            p.drawText(QRectF(i * slot, base + 3, slot, 16), Qt.AlignHCenter, lab)
            if v:
                p.setFont(mono)
                p.drawText(QRectF(i * slot, base - bh - 15, slot, 14), Qt.AlignHCenter, str(v))


class DotGrid(QWidget):
    """The workspace background: a dot lattice that echoes the logo."""

    def paintEvent(self, _):
        p = QPainter(self)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#222744"))
        step = 22
        for y in range(8, self.height(), step):
            for x in range(8, self.width(), step):
                p.drawEllipse(QPointF(x, y), 1.1, 1.1)
