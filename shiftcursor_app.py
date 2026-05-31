#!/usr/bin/env python3
"""
ShiftCursor — Windows to Linux Cursor Converter

A Material Design 3-inspired PySide6 desktop application that converts
Windows cursor themes (.cur/.ani) to Linux X11 format with an intuitive
drag-and-drop interface.
"""

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QFontDatabase, QIcon
from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow
from ui.resources import svg_to_pixmap


def main():
    # High DPI support
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("ShiftCursor")
    app.setOrganizationName("ShiftCursor")
    app.setApplicationDisplayName("ShiftCursor")

    # Set application icon
    app.setWindowIcon(QIcon(svg_to_pixmap("mouse_pointer", color="#00BFA5", size=64)))

    # Try to load Inter font (commonly available on modern Linux)
    font_families = ["Inter", "Segoe UI", "Roboto", "Helvetica Neue", "sans-serif"]
    app_font = QFont()
    for family in font_families:
        app_font.setFamily(family)
        if app_font.exactMatch():
            break
    app_font.setPointSize(10)
    app.setFont(app_font)

    # Create and show main window
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
