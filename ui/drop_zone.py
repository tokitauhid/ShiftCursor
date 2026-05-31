"""
ShiftCursor — Drag & Drop Zone Widget

Central drop zone with animated border, folder icon, and browse button.
Accepts folder drops and emits a signal with the list of paths.
"""

from pathlib import Path

from PySide6.QtCore import (
    Qt, Signal, QPropertyAnimation, QEasingCurve,
    Property, QTimer, QSize
)
from PySide6.QtGui import QPainter, QPen, QColor, QPainterPath, QFont
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QLabel, QPushButton, QFileDialog,
    QSizePolicy, QGraphicsOpacityEffect
)

from ui.resources import svg_to_pixmap


class DropZone(QFrame):
    """Drag-and-drop zone that accepts folder drops."""

    folders_dropped = Signal(list)  # List of Path objects

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("drop_zone_frame")
        self.setAcceptDrops(True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumHeight(180)

        # Animation state
        self._glow_opacity = 0.0
        self._is_drag_hover = False
        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(self._pulse_tick)
        self._pulse_phase = 0.0
        self._collapsed = False

        self._setup_ui()
        self._setup_animations()

    def _setup_ui(self):
        """Build the drop zone layout."""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(12)
        layout.setContentsMargins(40, 30, 40, 30)

        # Folder icon
        self._icon_label = QLabel()
        self._icon_label.setAlignment(Qt.AlignCenter)
        self._icon_label.setObjectName("drop_icon")
        self._update_icon("#6C6C84")
        layout.addWidget(self._icon_label)

        # Title
        self._title = QLabel("Drop cursor folders here")
        self._title.setObjectName("drop_title")
        self._title.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._title)

        # Subtitle
        self._subtitle = QLabel("or click Browse to select folders")
        self._subtitle.setObjectName("drop_subtitle")
        self._subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._subtitle)

        # Browse button
        self._browse_btn = QPushButton("  Browse Folders")
        self._browse_btn.setObjectName("browse_button")
        self._browse_btn.setCursor(Qt.PointingHandCursor)
        self._browse_btn.setFixedWidth(180)
        self._browse_btn.clicked.connect(self._on_browse)
        layout.addWidget(self._browse_btn, alignment=Qt.AlignCenter)

    def _update_icon(self, color: str):
        """Update the folder icon with the given color."""
        pixmap = svg_to_pixmap("folder_upload", color=color, size=48)
        self._icon_label.setPixmap(pixmap)

    def _setup_animations(self):
        """Setup the glow animation for drag hover."""
        self._glow_anim = QPropertyAnimation(self, b"glow_opacity")
        self._glow_anim.setDuration(300)
        self._glow_anim.setEasingCurve(QEasingCurve.InOutCubic)

    # ── Glow Property ───────────────────────────────────────
    def _get_glow_opacity(self):
        return self._glow_opacity

    def _set_glow_opacity(self, value):
        self._glow_opacity = value
        self.update()

    glow_opacity = Property(float, _get_glow_opacity, _set_glow_opacity)

    # ── Collapse / Expand ───────────────────────────────────
    def set_collapsed(self, collapsed: bool):
        """Collapse to a thin strip when folders are queued."""
        self._collapsed = collapsed
        if collapsed:
            self.setMinimumHeight(80)
            self.setMaximumHeight(100)
            self._title.setText("Drop more folders here")
            self._subtitle.hide()
            self._icon_label.hide()
        else:
            self.setMinimumHeight(180)
            self.setMaximumHeight(16777215)
            self._title.setText("Drop cursor folders here")
            self._subtitle.show()
            self._icon_label.show()

    # ── Drag Events ─────────────────────────────────────────
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            # Check if any URL is a directory
            has_dir = any(
                Path(url.toLocalFile()).is_dir()
                for url in event.mimeData().urls()
                if url.toLocalFile()
            )
            if has_dir:
                event.acceptProposedAction()
                self._start_hover()
                return
        event.ignore()

    def dragLeaveEvent(self, event):
        self._stop_hover()
        event.accept()

    def dropEvent(self, event):
        self._stop_hover()
        paths = []
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.is_dir():
                paths.append(path)
        if paths:
            self.folders_dropped.emit(paths)
            event.acceptProposedAction()
        else:
            event.ignore()

    def _start_hover(self):
        """Start the drag hover animation."""
        self._is_drag_hover = True
        self._update_icon("#00BFA5")
        self._glow_anim.stop()
        self._glow_anim.setStartValue(self._glow_opacity)
        self._glow_anim.setEndValue(1.0)
        self._glow_anim.start()
        self._pulse_timer.start(50)

    def _stop_hover(self):
        """Stop the drag hover animation."""
        self._is_drag_hover = False
        self._update_icon("#6C6C84")
        self._glow_anim.stop()
        self._glow_anim.setStartValue(self._glow_opacity)
        self._glow_anim.setEndValue(0.0)
        self._glow_anim.start()
        self._pulse_timer.stop()
        self._pulse_phase = 0.0

    def _pulse_tick(self):
        """Advance the border pulse animation."""
        import math
        self._pulse_phase += 0.08
        if self._pulse_phase > 2 * math.pi:
            self._pulse_phase -= 2 * math.pi
        self.update()

    # ── Paint ───────────────────────────────────────────────
    def paintEvent(self, event):
        super().paintEvent(event)

        if self._glow_opacity > 0.01:
            import math
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)

            # Pulsing glow border
            pulse = 0.6 + 0.4 * math.sin(self._pulse_phase)
            alpha = int(self._glow_opacity * pulse * 200)
            glow_color = QColor(0, 191, 165, alpha)

            pen = QPen(glow_color, 3)
            pen.setStyle(Qt.DashLine)
            pen.setDashPattern([8, 6])
            painter.setPen(pen)

            rect = self.rect().adjusted(4, 4, -4, -4)
            painter.drawRoundedRect(rect, 14, 14)

            # Outer glow
            glow_alpha = int(self._glow_opacity * pulse * 40)
            outer_color = QColor(0, 191, 165, glow_alpha)
            outer_pen = QPen(outer_color, 6)
            outer_pen.setStyle(Qt.SolidLine)
            painter.setPen(outer_pen)
            painter.drawRoundedRect(rect, 14, 14)

            painter.end()

    # ── Browse Button ───────────────────────────────────────
    def _on_browse(self):
        """Open a folder picker dialog."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Windows Cursor Folder",
            str(Path.home()),
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
        )
        if folder:
            self.folders_dropped.emit([Path(folder)])
