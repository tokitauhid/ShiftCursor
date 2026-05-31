"""
SetCursor — Main Window

Assembles the drop zone, folder card list, and action bar into
the main application window. Handles theme toggling and conversion orchestration.
"""

import json
from pathlib import Path

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QScrollArea, QFrame,
    QFileDialog, QMessageBox, QSizePolicy, QApplication
)

from core.converter import CursorConverter, ConversionResult
from core.worker import ConversionWorker
from ui.drop_zone import DropZone
from ui.folder_card import FolderCard, CardState
from ui.theme import DARK, LIGHT, COLORS, generate_stylesheet
from ui.resources import svg_to_pixmap, svg_to_icon


# Settings file path
SETTINGS_PATH = Path.home() / ".config" / "setcursor" / "settings.json"


class MainWindow(QMainWindow):
    """Main application window for SetCursor."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SetCursor")
        self.setMinimumSize(520, 460)
        self.resize(700, 620)

        # State
        self._theme = "dark"
        self._output_dir: Path | None = None
        self._folder_cards: list[FolderCard] = []
        self._worker: ConversionWorker | None = None
        self._is_converting = False

        # Load persisted settings
        self._load_settings()

        # Build UI
        self._setup_ui()
        self._apply_theme()

        # Check win2xcur availability
        self._check_dependencies()

    def _setup_ui(self):
        """Build the main window layout."""
        central = QWidget()
        self.setCentralWidget(central)

        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ── Title Bar ───────────────────────────────────────
        title_bar = QWidget()
        title_bar.setFixedHeight(60)
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(24, 12, 24, 12)

        # App icon + title
        icon_label = QLabel()
        icon_label.setPixmap(svg_to_pixmap("mouse_pointer", color="#00BFA5", size=24))
        icon_label.setFixedSize(28, 28)
        title_bar_layout.addWidget(icon_label)

        title = QLabel("SetCursor")
        title.setObjectName("title_label")
        title_bar_layout.addWidget(title)

        subtitle = QLabel("Windows → Linux Cursor Converter")
        subtitle.setObjectName("subtitle_label")
        title_bar_layout.addWidget(subtitle)

        title_bar_layout.addStretch()

        # Theme toggle
        self._theme_btn = QPushButton()
        self._theme_btn.setObjectName("theme_toggle")
        self._theme_btn.setCursor(Qt.PointingHandCursor)
        self._theme_btn.setToolTip("Toggle dark/light theme")
        self._theme_btn.clicked.connect(self._toggle_theme)
        title_bar_layout.addWidget(self._theme_btn)

        root_layout.addWidget(title_bar)

        # ── Content Area ────────────────────────────────────
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 8, 20, 8)
        content_layout.setSpacing(12)

        # Drop zone
        self._drop_zone = DropZone()
        self._drop_zone.folders_dropped.connect(self._on_folders_dropped)
        content_layout.addWidget(self._drop_zone)

        # Scroll area for folder cards
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setFrameShape(QFrame.NoFrame)

        self._cards_container = QWidget()
        self._cards_layout = QVBoxLayout(self._cards_container)
        self._cards_layout.setContentsMargins(0, 0, 0, 0)
        self._cards_layout.setSpacing(8)
        self._cards_layout.addStretch()

        self._scroll.setWidget(self._cards_container)
        self._scroll.hide()  # Hidden until folders are added
        content_layout.addWidget(self._scroll, stretch=1)

        root_layout.addWidget(content, stretch=1)

        # ── Bottom Action Bar ───────────────────────────────
        self._bottom_bar = QFrame()
        self._bottom_bar.setObjectName("bottom_bar")
        self._bottom_bar.setFixedHeight(64)
        self._bottom_bar.hide()  # Hidden until folders are added

        bottom_layout = QHBoxLayout(self._bottom_bar)
        bottom_layout.setContentsMargins(20, 10, 20, 10)
        bottom_layout.setSpacing(12)

        # Output directory button
        self._output_btn = QPushButton("📂  Choose Output Folder")
        self._output_btn.setObjectName("output_button")
        self._output_btn.setCursor(Qt.PointingHandCursor)
        self._output_btn.clicked.connect(self._choose_output_dir)
        bottom_layout.addWidget(self._output_btn)

        bottom_layout.addStretch()

        # Convert All button
        self._convert_btn = QPushButton("▶  Convert All")
        self._convert_btn.setObjectName("convert_button")
        self._convert_btn.setCursor(Qt.PointingHandCursor)
        self._convert_btn.clicked.connect(self._start_conversion)
        bottom_layout.addWidget(self._convert_btn)

        root_layout.addWidget(self._bottom_bar)

    # ── Theme ───────────────────────────────────────────────
    def _apply_theme(self):
        """Apply the current theme stylesheet."""
        theme_dict = DARK if self._theme == "dark" else LIGHT
        self.setStyleSheet(generate_stylesheet(theme_dict))

        # Update theme toggle icon
        if self._theme == "dark":
            self._theme_btn.setText("☀️")
            self._theme_btn.setToolTip("Switch to light theme")
        else:
            self._theme_btn.setText("🌙")
            self._theme_btn.setToolTip("Switch to dark theme")

    def _toggle_theme(self):
        """Toggle between dark and light themes."""
        self._theme = "light" if self._theme == "dark" else "dark"
        self._apply_theme()
        self._save_settings()

    # ── Folder Management ───────────────────────────────────
    def _on_folders_dropped(self, paths: list):
        """Handle folders being dropped or browsed."""
        for path in paths:
            # Skip duplicates
            if any(card.folder_path == path for card in self._folder_cards):
                continue

            card = FolderCard(path)
            card.remove_requested.connect(self._remove_card)
            card.install_requested.connect(self._install_theme)
            self._folder_cards.append(card)

            # Insert before the stretch
            idx = self._cards_layout.count() - 1
            self._cards_layout.insertWidget(idx, card)

        self._update_ui_state()

    def _remove_card(self, card: FolderCard):
        """Remove a folder card from the queue."""
        if card in self._folder_cards:
            self._folder_cards.remove(card)
            self._cards_layout.removeWidget(card)
            card.deleteLater()
        self._update_ui_state()

    def _update_ui_state(self):
        """Update UI elements based on the current queue state."""
        has_cards = len(self._folder_cards) > 0

        # Show/hide scroll area and bottom bar
        self._scroll.setVisible(has_cards)
        self._bottom_bar.setVisible(has_cards)

        # Collapse drop zone when cards exist
        self._drop_zone.set_collapsed(has_cards)

        # Update convert button state
        queued = sum(1 for c in self._folder_cards if c.state == CardState.QUEUED)
        self._convert_btn.setEnabled(queued > 0 and not self._is_converting)

        if self._is_converting:
            self._convert_btn.setText("⏳  Converting...")
        else:
            self._convert_btn.setText(f"▶  Convert All ({queued})" if queued > 0 else "▶  Convert All")

        # Update output button text
        if self._output_dir:
            dir_name = self._output_dir.name or str(self._output_dir)
            if len(dir_name) > 25:
                dir_name = "..." + dir_name[-22:]
            self._output_btn.setText(f"📂  {dir_name}")
            self._output_btn.setToolTip(str(self._output_dir))

    # ── Output Directory ────────────────────────────────────
    def _choose_output_dir(self):
        """Open a directory picker for the output folder."""
        start_dir = str(self._output_dir) if self._output_dir else str(Path.home())
        folder = QFileDialog.getExistingDirectory(
            self,
            "Choose Output Directory",
            start_dir,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
        )
        if folder:
            self._output_dir = Path(folder)
            self._update_ui_state()
            self._save_settings()

    # ── Conversion ──────────────────────────────────────────
    def _start_conversion(self):
        """Start batch conversion of all queued folders."""
        if self._is_converting:
            return

        # Require output directory
        if not self._output_dir:
            self._choose_output_dir()
            if not self._output_dir:
                return

        # Collect queued folders
        queued_cards = [c for c in self._folder_cards if c.state == CardState.QUEUED]
        if not queued_cards:
            return

        self._is_converting = True
        self._update_ui_state()

        # Mark all as converting
        for card in queued_cards:
            card.set_converting()

        # Map card indices to their positions
        self._active_cards = queued_cards

        # Create worker
        folders = [card.folder_path for card in queued_cards]
        self._worker = ConversionWorker(folders, self._output_dir, parent=self)
        self._worker.progress.connect(self._on_progress)
        self._worker.folder_done.connect(self._on_folder_done)
        self._worker.all_done.connect(self._on_all_done)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_progress(self, folder_idx: int, current: int, total: int, filename: str):
        """Handle progress update from worker."""
        if folder_idx < len(self._active_cards):
            self._active_cards[folder_idx].set_progress(current, total, filename)

    def _on_folder_done(self, folder_idx: int, result: ConversionResult):
        """Handle a single folder completing conversion."""
        if folder_idx < len(self._active_cards):
            card = self._active_cards[folder_idx]
            if result.success:
                card.set_done(result)
            else:
                card.set_error(result.error_message)

    def _on_all_done(self):
        """Handle all conversions completing."""
        self._is_converting = False
        self._worker = None
        self._update_ui_state()

    def _on_error(self, folder_idx: int, message: str):
        """Handle a conversion error."""
        if folder_idx < len(self._active_cards):
            self._active_cards[folder_idx].set_error(message)

    # ── Install ─────────────────────────────────────────────
    def _install_theme(self, result: ConversionResult):
        """Install a converted theme to the system."""
        success, message = CursorConverter.install_theme(result.output_path)

        if success:
            QMessageBox.information(
                self,
                "Theme Installed",
                f"✅ {result.output_path.name} has been installed!\n\n"
                f"{message}\n\n"
                "You can now select it in your Desktop Settings → Appearance → Cursor Theme."
            )
        else:
            QMessageBox.warning(
                self,
                "Installation Failed",
                f"❌ Could not install theme.\n\n{message}"
            )

    # ── Dependencies ────────────────────────────────────────
    def _check_dependencies(self):
        """Check if win2xcur is available."""
        converter = CursorConverter()
        if not converter.check_win2xcur():
            QMessageBox.warning(
                self,
                "Missing Dependency",
                "⚠️ 'win2xcur' is not installed.\n\n"
                "SetCursor requires win2xcur to convert Windows cursors.\n\n"
                "Install it with:\n"
                "  pip install win2xcur\n\n"
                "Or on Arch Linux:\n"
                "  yay -S python-win2xcur"
            )

    # ── Settings Persistence ────────────────────────────────
    def _load_settings(self):
        """Load persisted settings."""
        try:
            if SETTINGS_PATH.exists():
                data = json.loads(SETTINGS_PATH.read_text())
                self._theme = data.get("theme", "dark")
                output = data.get("output_dir")
                if output:
                    self._output_dir = Path(output)
        except Exception:
            pass

    def _save_settings(self):
        """Persist settings to disk."""
        try:
            SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "theme": self._theme,
                "output_dir": str(self._output_dir) if self._output_dir else None,
            }
            SETTINGS_PATH.write_text(json.dumps(data, indent=2))
        except Exception:
            pass

    # ── Close Event ─────────────────────────────────────────
    def closeEvent(self, event):
        """Cancel any running worker on close."""
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait(3000)
        self._save_settings()
        event.accept()
