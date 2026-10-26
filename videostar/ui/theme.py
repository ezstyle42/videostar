"""Application themes (dark / light) as Qt stylesheets."""

from __future__ import annotations

DARK = """
* { font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif; font-size: 14px; }
QMainWindow, QDialog { background: #1e1f26; color: #e6e6ea; }
QWidget { background: transparent; color: #e6e6ea; }
QLineEdit, QPlainTextEdit, QComboBox, QSpinBox {
    background: #2a2b35; border: 1px solid #3a3b47; border-radius: 8px;
    padding: 8px 10px; color: #e6e6ea; selection-background-color: #7c5cff;
}
QLineEdit:focus, QPlainTextEdit:focus, QComboBox:focus { border: 1px solid #7c5cff; }
QComboBox::drop-down { border: none; width: 24px; }
QComboBox QAbstractItemView { background: #2a2b35; border: 1px solid #3a3b47; selection-background-color: #7c5cff; }
QPushButton {
    background: #7c5cff; color: white; border: none; border-radius: 8px;
    padding: 9px 18px; font-weight: 600;
}
QPushButton:hover { background: #8f73ff; }
QPushButton:pressed { background: #6a4be0; }
QPushButton:disabled { background: #3a3b47; color: #8a8b95; }
QPushButton[flat="true"] { background: transparent; color: #b9bac5; font-weight: 500; }
QPushButton[flat="true"]:hover { background: #2a2b35; color: #ffffff; }
QPushButton[flat="true"]:checked { background: #34354a; color: #ffffff; }
QToolBar { background: #262833; border: none; spacing: 4px; padding: 6px; }
QListWidget { background: #232430; border: none; outline: none; }
QListWidget::item { padding: 6px; border-radius: 6px; }
QListWidget::item:selected { background: #34354a; }
QListWidget::item:hover { background: #2a2b35; }
QScrollArea { background: transparent; border: none; }
QProgressBar {
    background: #2a2b35; border: none; border-radius: 6px; height: 10px; text-align: center;
}
QProgressBar::chunk { background: #7c5cff; border-radius: 6px; }
QLabel[heading="true"] { font-size: 22px; font-weight: 700; color: #ffffff; }
QLabel[subtle="true"] { color: #9a9ba6; font-size: 13px; }
QLabel#cardTitle { font-weight: 600; color: #ffffff; }
QLabel#cardMeta { color: #9a9ba6; font-size: 12px; }
QFrame#card { background: #262833; border: 1px solid #34354a; border-radius: 12px; }
QFrame#dropZone {
    background: #232430; border: 2px dashed #4a4b5a; border-radius: 14px; color: #9a9ba6;
}
QFrame#dropZone:hover { border-color: #7c5cff; color: #c9c9d4; }
QFrame#sidebar { background: #262833; }
QStatusBar { background: #262833; color: #9a9ba6; }
QMenu { background: #2a2b35; border: 1px solid #3a3b47; }
QMenu::item:selected { background: #7c5cff; }
QTabWidget::pane { border: none; }
QCheckBox { spacing: 8px; }
QCheckBox::indicator { width: 18px; height: 18px; border-radius: 4px; border: 1px solid #4a4b5a; background: #2a2b35; }
QCheckBox::indicator:checked { background: #7c5cff; border-color: #7c5cff; }
QSlider::groove:horizontal { height: 6px; background: #2a2b35; border-radius: 3px; }
QSlider::handle:horizontal { background: #7c5cff; width: 14px; margin: -4px 0; border-radius: 7px; }
QScrollBar:vertical { background: transparent; width: 10px; }
QScrollBar::handle:vertical { background: #3a3b47; border-radius: 5px; min-height: 24px; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; }
QToolTip { background: #34354a; color: #e6e6ea; border: 1px solid #4a4b5a; padding: 6px; }
"""

LIGHT = """
* { font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif; font-size: 14px; }
QMainWindow, QDialog { background: #f4f5f8; color: #23242b; }
QWidget { background: transparent; color: #23242b; }
QLineEdit, QPlainTextEdit, QComboBox, QSpinBox {
    background: #ffffff; border: 1px solid #d5d6de; border-radius: 8px;
    padding: 8px 10px; color: #23242b; selection-background-color: #7c5cff; selection-color: white;
}
QLineEdit:focus, QPlainTextEdit:focus, QComboBox:focus { border: 1px solid #7c5cff; }
QComboBox::drop-down { border: none; width: 24px; }
QComboBox QAbstractItemView {
    background: #ffffff; border: 1px solid #d5d6de;
    selection-background-color: #7c5cff; selection-color: white;
}
QPushButton {
    background: #7c5cff; color: white; border: none; border-radius: 8px;
    padding: 9px 18px; font-weight: 600;
}
QPushButton:hover { background: #8f73ff; }
QPushButton:pressed { background: #6a4be0; }
QPushButton:disabled { background: #d5d6de; color: #9a9ba6; }
QPushButton[flat="true"] { background: transparent; color: #5c5d68; font-weight: 500; }
QPushButton[flat="true"]:hover { background: #e8e9ef; color: #23242b; }
QPushButton[flat="true"]:checked { background: #dcd7ff; color: #4a35c9; }
QToolBar { background: #ffffff; border: none; spacing: 4px; padding: 6px; }
QListWidget { background: #ffffff; border: none; outline: none; }
QListWidget::item { padding: 6px; border-radius: 6px; }
QListWidget::item:selected { background: #dcd7ff; }
QListWidget::item:hover { background: #eceef4; }
QScrollArea { background: transparent; border: none; }
QProgressBar { background: #e4e5ec; border: none; border-radius: 6px; height: 10px; text-align: center; }
QProgressBar::chunk { background: #7c5cff; border-radius: 6px; }
QLabel[heading="true"] { font-size: 22px; font-weight: 700; color: #17181d; }
QLabel[subtle="true"] { color: #6c6d78; font-size: 13px; }
QLabel#cardTitle { font-weight: 600; color: #17181d; }
QLabel#cardMeta { color: #6c6d78; font-size: 12px; }
QFrame#card { background: #ffffff; border: 1px solid #e0e1e8; border-radius: 12px; }
QFrame#dropZone {
    background: #ffffff; border: 2px dashed #c3c4cf; border-radius: 14px; color: #6c6d78;
}
QFrame#dropZone:hover { border-color: #7c5cff; color: #4a35c9; }
QFrame#sidebar { background: #ffffff; }
QStatusBar { background: #ffffff; color: #6c6d78; }
QMenu { background: #ffffff; border: 1px solid #d5d6de; }
QMenu::item:selected { background: #7c5cff; color: white; }
QTabWidget::pane { border: none; }
QCheckBox { spacing: 8px; }
QCheckBox::indicator { width: 18px; height: 18px; border-radius: 4px; border: 1px solid #c3c4cf; background: #ffffff; }
QCheckBox::indicator:checked { background: #7c5cff; border-color: #7c5cff; }
QSlider::groove:horizontal { height: 6px; background: #e4e5ec; border-radius: 3px; }
QSlider::handle:horizontal { background: #7c5cff; width: 14px; margin: -4px 0; border-radius: 7px; }
QScrollBar:vertical { background: transparent; width: 10px; }
QScrollBar::handle:vertical { background: #c3c4cf; border-radius: 5px; min-height: 24px; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; }
QToolTip { background: #34354a; color: #e6e6ea; border: 1px solid #4a4b5a; padding: 6px; }
"""


def stylesheet(theme: str) -> str:
    return DARK if theme == "dark" else LIGHT


def apply_theme(app, theme: str) -> None:
    app.setStyleSheet(stylesheet(theme))
