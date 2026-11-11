"""Colours and the application stylesheet."""
from string import Template

C = dict(
    ground="#0b0d18", panel="#131628", panel2="#1a1e35", line="#262b47", line2="#343a5e",
    text="#e9ebf5", muted="#8b90ad", accent="#7c8cff", accent2="#4fd1e8",
    ok="#5fd3a0", warn="#f2b75c", bad="#ff6b7a",
)
FONT = "Segoe UI"
MONO = "Cascadia Mono"

QSS = Template("""
* { font-family: "$font", "Helvetica Neue", Arial, sans-serif; font-size: 14px; color: $text; }
QMainWindow, QDialog, QMessageBox { background: $ground; }
QToolTip { background: $panel2; color: $text; border: 1px solid $line2; padding: 4px 8px; }

QScrollArea, QScrollArea > QWidget > QWidget { background: transparent; border: 0; }
QScrollBar:vertical { background: transparent; width: 10px; margin: 0; }
QScrollBar::handle:vertical { background: $line2; border-radius: 5px; min-height: 30px; }
QScrollBar:horizontal { background: transparent; height: 10px; }
QScrollBar::handle:horizontal { background: $line2; border-radius: 5px; min-width: 30px; }
QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }

QLabel { background: transparent; }
QLabel#h1 { font-size: 28px; font-weight: 600; }
QLabel#h2 { font-size: 16px; font-weight: 600; }
QLabel#muted, QLabel[muted="true"] { color: $muted; }
QLabel#mono { font-family: "$mono", Consolas, monospace; }
QLabel#statValue { font-family: "$mono", Consolas, monospace; font-size: 30px; font-weight: 600; }
QLabel[chip="true"] { border: 1px solid $line2; border-radius: 11px; padding: 0 10px; color: $muted; font-size: 12px; }
QLabel[chip="accent"] { border: 1px solid $accent; border-radius: 11px; padding: 0 10px; color: $accent; font-size: 12px; }
QLabel[chip="ok"] { border: 1px solid $ok; border-radius: 11px; padding: 0 10px; color: $ok; font-size: 12px; }
QLabel[chip="warn"] { border: 1px solid $warn; border-radius: 11px; padding: 0 10px; color: $warn; font-size: 12px; }
QLabel[chip="bad"] { border: 1px solid $bad; border-radius: 11px; padding: 0 10px; color: $bad; font-size: 12px; }
QLabel#courseIcon { background: $panel2; border: 1px solid $line2; border-radius: 10px; font-size: 18px; font-weight: 600; color: $accent; }

QLineEdit, QPlainTextEdit, QTextEdit, QTextBrowser, QComboBox, QSpinBox, QDateEdit, QTimeEdit {
  background: $ground; border: 1px solid $line2; border-radius: 8px; padding: 6px 10px;
  selection-background-color: #3a4388; }
QLineEdit:focus, QPlainTextEdit:focus, QComboBox:focus, QSpinBox:focus, QDateEdit:focus, QTimeEdit:focus { border-color: $accent; }
QTextBrowser { border-color: $line; }
QComboBox::drop-down { border: 0; width: 22px; }
QComboBox QAbstractItemView { background: $panel2; border: 1px solid $line2; selection-background-color: #2b3160; outline: 0; }

QPushButton { background: $panel2; border: 1px solid $line2; border-radius: 8px; padding: 7px 14px; }
QPushButton:hover { border-color: $accent; }
QPushButton:disabled { color: #5b607c; border-color: $line; }
QPushButton[variant="primary"] { background: $accent; border-color: $accent; color: #0b0d18; font-weight: 600; }
QPushButton[variant="primary"]:hover { background: #95a2ff; }
QPushButton[variant="primary"]:disabled { background: #3b4170; border-color: #3b4170; color: #8d92b5; }
QPushButton[variant="danger"] { color: $bad; }
QPushButton[variant="danger"]:hover { border-color: $bad; }
QPushButton[variant="ghost"] { background: transparent; border-color: transparent; color: $muted; }
QPushButton[variant="ghost"]:hover { color: $text; border-color: $line2; }
QPushButton[variant="link"] { background: transparent; border: 0; color: $accent2; padding: 2px 4px; text-align: left; }
QPushButton[variant="link"]:hover { text-decoration: underline; }
QPushButton[size="sm"] { padding: 3px 10px; font-size: 13px; }
QPushButton#aiPill { background: $panel; border-radius: 14px; padding: 4px 14px; color: $muted; font-size: 13px; }

QToolButton#dock { background: transparent; border: 0; border-radius: 10px; padding: 9px 2px 6px 2px; color: $muted; font-size: 11px; }
QToolButton#dock:hover { background: $panel; color: $text; }
QToolButton#dock:checked { background: $panel2; color: $text; }

QListWidget { background: transparent; border: 0; outline: 0; }
QListWidget::item { padding: 8px 10px; border-radius: 8px; margin: 1px 0; }
QListWidget::item:hover { background: $panel2; }
QListWidget::item:selected { background: #262c58; color: $text; }

QCheckBox, QRadioButton { spacing: 8px; background: transparent; }
QCheckBox::indicator { width: 16px; height: 16px; border: 1px solid $line2; border-radius: 4px; background: $ground; }
QCheckBox::indicator:checked { background: $accent; border-color: $accent; }
QRadioButton::indicator { width: 14px; height: 14px; border: 1px solid $line2; border-radius: 8px; background: $ground; }
QRadioButton::indicator:checked { background: $accent; border-color: $accent; }

QProgressBar { background: $line; border: 0; border-radius: 3px; max-height: 6px; min-height: 6px; text-align: center; }
QProgressBar::chunk { background: $accent; border-radius: 3px; }
QSlider::groove:horizontal { height: 6px; background: $line; border-radius: 3px; }
QSlider::sub-page:horizontal { background: $accent; border-radius: 3px; }
QSlider::handle:horizontal { width: 14px; margin: -5px 0; border-radius: 7px; background: $text; }

QFrame#quizOption { background: $panel2; border: 1px solid $line2; border-radius: 8px; }
QPushButton[state="right"] { border-color: $ok; color: $ok; }
QPushButton[state="wrong"] { border-color: $bad; color: $bad; }
QFrame#flashCard { background: $panel2; border: 1px solid $accent; border-radius: 14px; }
QSplitter::handle { background: transparent; }
""").substitute(font=FONT, mono=MONO, **C)
