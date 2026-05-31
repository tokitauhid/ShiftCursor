"""
ShiftCursor — QThread Worker for Background Conversion

Runs cursor conversion in a background thread, emitting signals
for progress updates to the GUI.
"""

from pathlib import Path

from PySide6.QtCore import QThread, Signal

from core.converter import CursorConverter, ConversionResult


class ConversionWorker(QThread):
    """Background worker that processes a batch of cursor folder conversions."""

    # Signals
    progress = Signal(int, int, int, str)       # (folder_index, current, total, filename)
    folder_done = Signal(int, ConversionResult)  # (folder_index, result)
    all_done = Signal()                          # All folders processed
    error = Signal(int, str)                     # (folder_index, error_message)

    def __init__(self, folders: list, output_dir: Path, parent=None):
        """
        Args:
            folders: List of Path objects (input cursor folders)
            output_dir: Parent directory for all output themes
        """
        super().__init__(parent)
        self.folders = folders
        self.output_dir = output_dir
        self.converter = CursorConverter()
        self._cancelled = False

    def cancel(self):
        """Request cancellation of the entire batch."""
        self._cancelled = True
        self.converter.cancel()

    def run(self):
        """Process all folders in sequence."""
        for idx, folder_path in enumerate(self.folders):
            if self._cancelled:
                break

            try:
                def on_progress(current, total, filename, _idx=idx):
                    self.progress.emit(_idx, current, total, filename)

                result = self.converter.convert_folder(
                    input_path=folder_path,
                    output_dir=self.output_dir,
                    on_progress=on_progress,
                )

                if self._cancelled:
                    break

                self.folder_done.emit(idx, result)

            except Exception as e:
                self.error.emit(idx, str(e))

        if not self._cancelled:
            self.all_done.emit()
