"""
SetCursor — Core Converter Module

Refactored conversion logic from convert_cursors.py into an importable class
with progress callbacks for GUI integration.
"""

import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional


# Common mapping from Windows cursor filenames (without extension) to Linux X11 names
WINDOWS_TO_LINUX_MAP = {
    "arrow": ["left_ptr", "default", "arrow"],
    "normal select": ["left_ptr", "default", "arrow"],
    "help": ["help", "question_arrow"],
    "help select": ["help", "question_arrow"],
    "appstarting": ["left_ptr_watch", "half-busy", "progress"],
    "working in background": ["left_ptr_watch", "half-busy", "progress"],
    "wait": ["watch", "wait", "busy"],
    "busy": ["watch", "wait", "busy"],
    "cross": ["cross", "crosshair", "cross_reverse"],
    "precision select": ["cross", "crosshair", "cross_reverse"],
    "ibeam": ["xterm", "text", "ibeam"],
    "text select": ["xterm", "text", "ibeam"],
    "nwpen": ["pencil", "draft"],
    "handwriting": ["pencil", "draft"],
    "no": ["crossed_circle", "not-allowed", "circle", "no-drop", "dnd-none"],
    "unavailable": ["crossed_circle", "not-allowed", "circle", "no-drop", "dnd-none"],
    "sizens": ["sb_v_double_arrow", "size_ver", "n-resize", "s-resize", "ns-resize", "row-resize"],
    "vertical resize": ["sb_v_double_arrow", "size_ver", "n-resize", "s-resize", "ns-resize", "row-resize"],
    "sizewe": ["sb_h_double_arrow", "size_hor", "e-resize", "w-resize", "ew-resize", "col-resize"],
    "horizontal resize": ["sb_h_double_arrow", "size_hor", "e-resize", "w-resize", "ew-resize", "col-resize"],
    "sizenwse": ["size_fdiag", "nw-resize", "se-resize", "nwse-resize", "top_left_corner", "bottom_right_corner"],
    "diagonal resize 1": ["size_fdiag", "nw-resize", "se-resize", "nwse-resize", "top_left_corner", "bottom_right_corner"],
    "sizenesw": ["size_bdiag", "ne-resize", "sw-resize", "nesw-resize", "top_right_corner", "bottom_left_corner"],
    "diagonal resize 2": ["size_bdiag", "ne-resize", "sw-resize", "nesw-resize", "top_right_corner", "bottom_left_corner"],
    "sizeall": ["fleur", "size_all", "move", "all-scroll", "dnd-move"],
    "move": ["fleur", "size_all", "move", "all-scroll", "dnd-move"],
    "uparrow": ["up_arrow", "center_ptr"],
    "alternate select": ["up_arrow", "center_ptr"],
    "hand": ["pointer", "hand", "hand2", "link", "grab", "grabbing", "dnd-link"],
    "link": ["pointer", "hand", "hand2", "link", "grab", "grabbing", "dnd-link"],
    "link select": ["pointer", "hand", "hand2", "link", "grab", "grabbing", "dnd-link"],
    "pin": ["pin", "alias"],
    "person": ["person", "dnd-ask"],
}

# Mapping from Windows .inf file variables to Linux X11 names
INF_TO_LINUX_MAP = {
    "pointer": ["left_ptr", "default", "arrow"],
    "help": ["help", "question_arrow"],
    "work": ["left_ptr_watch", "half-busy", "progress"],
    "busy": ["watch", "wait", "busy"],
    "cross": ["cross", "crosshair", "cross_reverse"],
    "text": ["xterm", "text", "ibeam"],
    "hand": ["pencil", "draft"],
    "unavailiable": ["crossed_circle", "not-allowed", "circle", "no-drop", "dnd-none"],
    "unavailable": ["crossed_circle", "not-allowed", "circle", "no-drop", "dnd-none"],
    "vert": ["sb_v_double_arrow", "size_ver", "n-resize", "s-resize", "ns-resize", "row-resize"],
    "horz": ["sb_h_double_arrow", "size_hor", "e-resize", "w-resize", "ew-resize", "col-resize"],
    "dgn1": ["size_fdiag", "nw-resize", "se-resize", "nwse-resize", "top_left_corner", "bottom_right_corner"],
    "dgn2": ["size_bdiag", "ne-resize", "sw-resize", "nesw-resize", "top_right_corner", "bottom_left_corner"],
    "move": ["fleur", "size_all", "move", "all-scroll", "dnd-move"],
    "alternate": ["up_arrow", "center_ptr"],
    "link": ["pointer", "hand", "hand2", "link", "grab", "grabbing", "dnd-link"],
    "pin": ["pin", "alias"],
    "person": ["person", "dnd-ask"],
}

# Secondary aliases: map additional cursor names to existing ones
SECONDARY_ALIASES = {
    "context-menu": ["left_ptr", "default", "arrow"],
    "copy": ["left_ptr", "default", "arrow"],
    "dnd-copy": ["left_ptr", "default", "arrow"],
    "cell": ["cross", "crosshair"],
    "vertical-text": ["xterm", "text", "ibeam"],
    "zoom-in": ["cross", "crosshair", "left_ptr"],
    "zoom-out": ["cross", "crosshair", "left_ptr"],
    "pirate": ["crossed_circle", "not-allowed", "circle"],
}


@dataclass
class ConversionResult:
    """Result of a cursor folder conversion."""
    input_path: Path
    output_path: Path
    converted_count: int = 0
    failed_count: int = 0
    symlink_count: int = 0
    ani_count: int = 0
    cur_count: int = 0
    total_files: int = 0
    unmapped_files: list = field(default_factory=list)
    cursor_files_list: list = field(default_factory=list)
    success: bool = True
    error_message: str = ""


class CursorConverter:
    """Converts Windows cursor themes to Linux X11 format."""

    def __init__(self):
        self._cancelled = False

    def cancel(self):
        """Request cancellation of the current conversion."""
        self._cancelled = True

    def check_win2xcur(self) -> bool:
        """Check if win2xcur is installed and available."""
        try:
            subprocess.run(
                ["win2xcur", "--help"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except FileNotFoundError:
            return False

    @staticmethod
    def read_inf_file(inf_path: Path) -> str:
        """Read an .inf file trying multiple encodings for robustness."""
        for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
            try:
                return inf_path.read_text(encoding=encoding)
            except (UnicodeDecodeError, UnicodeError):
                continue
        return inf_path.read_text(encoding="utf-8", errors="ignore")

    @staticmethod
    def parse_inf_mapping(inf_file: Path) -> dict:
        """Parse the [Strings] section of an .inf file into a cursor mapping dict."""
        inf_mapping = {}
        content = CursorConverter.read_inf_file(inf_file)
        in_strings_section = False

        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith(";"):
                continue
            if line.startswith("[") and line.endswith("]"):
                in_strings_section = line.lower() == "[strings]"
                continue

            if in_strings_section and "=" in line:
                key, val = line.split("=", 1)
                key = key.strip().lower()
                val = val.strip().strip('"').strip()

                stem = Path(val).stem.lower()
                if key in INF_TO_LINUX_MAP:
                    inf_mapping[stem] = INF_TO_LINUX_MAP[key]

        return inf_mapping

    @staticmethod
    def match_cursor_name(stem: str, mapping: dict) -> list:
        """Match a cursor file stem against a name mapping dict."""
        if stem in mapping:
            return mapping[stem]

        sorted_keys = sorted(mapping.keys(), key=len, reverse=True)
        for key in sorted_keys:
            if key in stem:
                return mapping[key]

        return []

    @staticmethod
    def sanitize_theme_name(name: str) -> str:
        """Sanitize a folder name into a safe theme name for Linux cursor themes."""
        return re.sub(r"[^a-zA-Z0-9_\-]", "_", name)

    def scan_folder(self, input_path: Path) -> tuple:
        """Scan a folder and return (cursor_files, ani_count, cur_count)."""
        cursor_files = list(input_path.glob("*.cur")) + list(input_path.glob("*.ani"))
        # Also check case-insensitive
        cursor_files += [f for f in input_path.glob("*.CUR") if f not in cursor_files]
        cursor_files += [f for f in input_path.glob("*.ANI") if f not in cursor_files]

        ani_count = sum(1 for f in cursor_files if f.suffix.lower() == ".ani")
        cur_count = sum(1 for f in cursor_files if f.suffix.lower() == ".cur")

        return cursor_files, ani_count, cur_count

    def convert_folder(
        self,
        input_path: Path,
        output_dir: Path,
        on_progress: Optional[Callable[[int, int, str], None]] = None,
    ) -> ConversionResult:
        """
        Convert a Windows cursor folder to Linux format.

        Args:
            input_path: Path to the Windows cursor folder
            output_dir: Parent directory where the output theme folder will be created
            on_progress: Callback(current, total, filename) for progress updates

        Returns:
            ConversionResult with conversion statistics
        """
        self._cancelled = False

        # Build output path
        base_theme_name = self.sanitize_theme_name(input_path.name) + "_linux"
        output_path = output_dir / base_theme_name

        # Avoid overwriting existing folders
        if output_path.exists():
            counter = 2
            while (output_dir / f"{base_theme_name}_{counter}").exists():
                counter += 1
            output_path = output_dir / f"{base_theme_name}_{counter}"

        result = ConversionResult(input_path=input_path, output_path=output_path)

        # Scan for cursor files
        cursor_files, ani_count, cur_count = self.scan_folder(input_path)
        result.ani_count = ani_count
        result.cur_count = cur_count
        result.total_files = len(cursor_files)
        result.cursor_files_list = [f.name for f in cursor_files]

        if not cursor_files:
            result.success = False
            result.error_message = f"No .cur or .ani files found in {input_path.name}"
            return result

        # Create output directories
        cursors_dir = output_path / "cursors"
        try:
            cursors_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            result.success = False
            result.error_message = f"Cannot create output directory: {e}"
            return result

        # Convert each file
        for i, cursor_file in enumerate(cursor_files):
            if self._cancelled:
                result.error_message = "Conversion cancelled"
                result.success = False
                return result

            if on_progress:
                on_progress(i, len(cursor_files), cursor_file.name)

            try:
                proc = subprocess.run(
                    ["win2xcur", str(cursor_file), "-o", str(cursors_dir)],
                    capture_output=True,
                    text=True,
                )
                if proc.returncode != 0:
                    result.failed_count += 1
                else:
                    result.converted_count += 1
            except Exception:
                result.failed_count += 1

        # Final progress callback
        if on_progress:
            on_progress(len(cursor_files), len(cursor_files), "Done")

        # Parse .inf for mappings
        inf_mapping = {}
        inf_files = list(input_path.glob("*.inf"))
        if inf_files:
            try:
                inf_mapping = self.parse_inf_mapping(inf_files[0])
            except Exception:
                inf_mapping = {}

        # Create symlinks
        for generated_file in cursors_dir.iterdir():
            if not generated_file.is_file():
                continue

            stem = generated_file.stem.lower()
            linux_names = []

            if inf_mapping and stem in inf_mapping:
                linux_names = inf_mapping[stem]
            else:
                linux_names = self.match_cursor_name(stem, WINDOWS_TO_LINUX_MAP)

            if not linux_names:
                result.unmapped_files.append(generated_file.name)

            for linux_name in linux_names:
                symlink_path = cursors_dir / linux_name
                if not symlink_path.exists():
                    try:
                        symlink_path.symlink_to(generated_file.name)
                        result.symlink_count += 1
                    except Exception:
                        pass

        # Secondary aliases
        for alias_name, targets in SECONDARY_ALIASES.items():
            alias_path = cursors_dir / alias_name
            if alias_path.exists():
                continue
            for target in targets:
                target_path = cursors_dir / target
                if target_path.exists():
                    try:
                        real_name = target_path.resolve().name
                        alias_path.symlink_to(real_name)
                        result.symlink_count += 1
                    except Exception:
                        pass
                    break

        # Create index.theme
        theme_name = output_path.name
        theme_content = f"""[Icon Theme]
Name={theme_name}
Comment=Converted from Windows Cursor Theme ({input_path.name})
Inherits=default
"""
        (output_path / "index.theme").write_text(theme_content)

        return result

    @staticmethod
    def install_theme(output_path: Path) -> tuple:
        """
        Install a converted cursor theme to ~/.local/share/icons/.

        Returns:
            (success: bool, message: str)
        """
        icons_dir = Path.home() / ".local" / "share" / "icons"
        dest = icons_dir / output_path.name

        try:
            icons_dir.mkdir(parents=True, exist_ok=True)

            if dest.exists():
                import shutil
                shutil.rmtree(dest)

            import shutil
            shutil.copytree(output_path, dest, symlinks=True)

            return True, f"Installed to {dest}"
        except Exception as e:
            return False, f"Installation failed: {e}"
