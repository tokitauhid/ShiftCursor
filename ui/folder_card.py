"""
ShiftCursor — Folder Card Widget

Material Design 3 card showing a queued/converting/done folder with
progress bar, status indicators, and expandable details.
"""

import subprocess
from enum import Enum
from pathlib import Path

from PySide6.QtCore import (
    Qt, Signal, QPropertyAnimation, QEasingCurve, Property, QSize
)
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar, QSizePolicy, QWidget,
    QGraphicsOpacityEffect
)

from core.converter import ConversionResult, CursorConverter
from ui.resources import svg_to_pixmap


class CardState(Enum):
    QUEUED = "queued"
    CONVERTING = "converting"
    DONE = "done"
    ERROR = "error"


class FolderCard(QFrame):
    """Card widget representing a single cursor folder in the queue."""

    remove_requested = Signal(object)  # self
    install_requested = Signal(object)  # ConversionResult

    def __init__(self, folder_path: Path, parent=None):
        super().__init__(parent)
        self.folder_path = folder_path
        self.state = CardState.QUEUED
        self.result: ConversionResult | None = None
        self._expanded = False

        self.setObjectName("folder_card")
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # Scan folder for file counts
        converter = CursorConverter()
        files, self._ani_count, self._cur_count = converter.scan_folder(folder_path)
        self._total_files = len(files)

        self._setup_ui()
        self._update_state()

    def _setup_ui(self):
        """Build the card layout."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 14, 16, 14)
        main_layout.setSpacing(8)

        # ── Top Row: icon + name + status + remove ──
        top_row = QHBoxLayout()
        top_row.setSpacing(12)

        # Folder icon
        self._icon_label = QLabel()
        self._icon_label.setFixedSize(32, 32)
        self._icon_label.setPixmap(svg_to_pixmap("folder", color="#00BFA5", size=28))
        self._icon_label.setAlignment(Qt.AlignCenter)
        top_row.addWidget(self._icon_label)

        # Name + info column
        name_col = QVBoxLayout()
        name_col.setSpacing(2)

        self._name_label = QLabel(self.folder_path.name)
        self._name_label.setObjectName("card_name")
        self._name_label.setWordWrap(True)
        name_col.addWidget(self._name_label)

        info_text = f"{self._ani_count} .ani, {self._cur_count} .cur"
        if self._total_files == 0:
            info_text = "No cursor files found"
        self._info_label = QLabel(info_text)
        self._info_label.setObjectName("card_info")
        name_col.addWidget(self._info_label)

        top_row.addLayout(name_col, stretch=1)

        # Status label
        self._status_label = QLabel("⏳ Queued")
        self._status_label.setObjectName("card_status")
        top_row.addWidget(self._status_label)

        # Remove button
        self._remove_btn = QPushButton("✕")
        self._remove_btn.setObjectName("remove_button")
        self._remove_btn.setFixedSize(28, 28)
        self._remove_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self._remove_btn.setToolTip("Remove from queue")
        self._remove_btn.clicked.connect(lambda: self.remove_requested.emit(self))
        top_row.addWidget(self._remove_btn)

        main_layout.addLayout(top_row)

        # ── Progress bar ──
        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setTextVisible(False)
        self._progress.setFixedHeight(6)
        self._progress.hide()
        main_layout.addWidget(self._progress)

        # ── Expandable Details Section ──
        self._details_widget = QWidget()
        self._details_widget.hide()
        details_layout = QVBoxLayout(self._details_widget)
        details_layout.setContentsMargins(0, 4, 0, 0)
        details_layout.setSpacing(8)

        # Separator
        sep = QFrame()
        sep.setObjectName("separator")
        sep.setFrameShape(QFrame.HLine)
        details_layout.addWidget(sep)

        # Result summary
        self._result_label = QLabel()
        self._result_label.setObjectName("result_summary")
        self._result_label.setWordWrap(True)
        details_layout.addWidget(self._result_label)

        # Output path
        self._path_label = QLabel()
        self._path_label.setObjectName("output_path_label")
        self._path_label.setWordWrap(True)
        self._path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        details_layout.addWidget(self._path_label)

        # Action buttons row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self._install_btn = QPushButton("  Install to System")
        self._install_btn.setObjectName("install_button")
        self._install_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self._install_btn.clicked.connect(self._on_install)
        btn_row.addWidget(self._install_btn)

        self._open_btn = QPushButton("  Open Folder")
        self._open_btn.setObjectName("open_folder_button")
        self._open_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self._open_btn.clicked.connect(self._on_open_folder)
        btn_row.addWidget(self._open_btn)

        btn_row.addStretch()
        details_layout.addLayout(btn_row)

        main_layout.addWidget(self._details_widget)

    def _update_state(self):
        """Update visual state based on current card state."""
        status_map = {
            CardState.QUEUED: ("⏳  Queued", "status_queued"),
            CardState.CONVERTING: ("🔄  Converting...", "status_converting"),
            CardState.DONE: ("✅  Done", "status_done"),
            CardState.ERROR: ("❌  Error", "status_error"),
        }
        text, obj_name = status_map[self.state]
        self._status_label.setText(text)
        self._status_label.setObjectName("card_status")
        # Apply sub-style via additional object name
        self._status_label.setProperty("status", self.state.value)

        # Show/hide progress bar
        if self.state == CardState.CONVERTING:
            self._progress.show()
            self._remove_btn.setEnabled(False)
        elif self.state in (CardState.DONE, CardState.ERROR):
            self._progress.hide()
            self._remove_btn.setEnabled(True)

        # Re-apply status color directly since QSS property selectors are limited
        color_map = {
            CardState.QUEUED: "#6C6C84",
            CardState.CONVERTING: "#00BFA5",
            CardState.DONE: "#4CAF50",
            CardState.ERROR: "#EF5350",
        }
        self._status_label.setStyleSheet(
            f"color: {color_map[self.state]}; font-weight: 600; font-size: 11px; background: transparent;"
        )

    # ── Public API ──────────────────────────────────────────
    def set_converting(self):
        """Mark this card as currently converting."""
        self.state = CardState.CONVERTING
        self._update_state()

    def set_progress(self, current: int, total: int, filename: str):
        """Update the progress bar."""
        if total > 0:
            pct = int((current / total) * 100)
            self._progress.setValue(pct)
        self._info_label.setText(f"Converting: {filename}")

    def set_done(self, result: ConversionResult):
        """Mark conversion as complete with results."""
        self.result = result
        self.state = CardState.DONE
        self._update_state()

        # Update info text
        self._info_label.setText(
            f"{result.converted_count} converted, "
            f"{result.symlink_count} symlinks, "
            f"{result.failed_count} failed"
        )

        # Update icon
        self._icon_label.setPixmap(
            svg_to_pixmap("check_circle", color="#4CAF50", size=28)
        )

        # Populate details
        summary_parts = [
            f"✓ {result.converted_count} cursor files converted",
            f"✓ {result.symlink_count} Linux symlinks created",
        ]
        if result.failed_count > 0:
            summary_parts.append(f"✗ {result.failed_count} files failed")
        if result.unmapped_files:
            summary_parts.append(f"⚠ {len(result.unmapped_files)} files unmapped")

        self._result_label.setText("\n".join(summary_parts))
        self._path_label.setText(f"📂 Output: {result.output_path}")

        # Auto-expand on completion
        self._set_expanded(True)

    def set_error(self, message: str):
        """Mark conversion as failed."""
        self.state = CardState.ERROR
        self._update_state()
        self._info_label.setText(message)
        self._icon_label.setPixmap(
            svg_to_pixmap("x_circle", color="#EF5350", size=28)
        )

    # ── Expand / Collapse ───────────────────────────────────
    def mousePressEvent(self, event):
        """Toggle expansion on click (only when done/error)."""
        if self.state in (CardState.DONE, CardState.ERROR) and event.button() == Qt.LeftButton:
            self._set_expanded(not self._expanded)
        super().mousePressEvent(event)

    def _set_expanded(self, expanded: bool):
        """Show or hide the details section."""
        self._expanded = expanded
        self._details_widget.setVisible(expanded)

    # ── Actions ─────────────────────────────────────────────
    def _on_install(self):
        """Install the converted theme to the system."""
        if self.result:
            self.install_requested.emit(self.result)

    def _on_open_folder(self):
        """Open the output folder in the file manager."""
        if self.result and self.result.output_path.exists():
            try:
                subprocess.Popen(["xdg-open", str(self.result.output_path)])
            except Exception:
                pass
