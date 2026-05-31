import os
import sys
import re
import subprocess
from pathlib import Path

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
    "person": ["person", "dnd-ask"]
}

# Mapping from Windows .inf file variables to Linux X11 names
INF_TO_LINUX_MAP = {
    "pointer": ["left_ptr", "default", "arrow"],
    "help": ["help", "question_arrow"],
    "work": ["left_ptr_watch", "half-busy", "progress"],
    "busy": ["watch", "wait", "busy"],
    "cross": ["cross", "crosshair", "cross_reverse"],
    "text": ["xterm", "text", "ibeam"],
    "hand": ["pencil", "draft"],  # 'hand' in .inf is handwriting
    "unavailiable": ["crossed_circle", "not-allowed", "circle", "no-drop", "dnd-none"],  # common typo in .inf
    "unavailable": ["crossed_circle", "not-allowed", "circle", "no-drop", "dnd-none"],
    "vert": ["sb_v_double_arrow", "size_ver", "n-resize", "s-resize", "ns-resize", "row-resize"],
    "horz": ["sb_h_double_arrow", "size_hor", "e-resize", "w-resize", "ew-resize", "col-resize"],
    "dgn1": ["size_fdiag", "nw-resize", "se-resize", "nwse-resize", "top_left_corner", "bottom_right_corner"],
    "dgn2": ["size_bdiag", "ne-resize", "sw-resize", "nesw-resize", "top_right_corner", "bottom_left_corner"],
    "move": ["fleur", "size_all", "move", "all-scroll", "dnd-move"],
    "alternate": ["up_arrow", "center_ptr"],
    "link": ["pointer", "hand", "hand2", "link", "grab", "grabbing", "dnd-link"],
    "pin": ["pin", "alias"],
    "person": ["person", "dnd-ask"]
}

# Secondary aliases: map additional cursor names to existing ones.
# These are created as symlinks pointing to the first existing target found.
# Format: "alias_name": ["preferred_target", "fallback_target", ...]
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


def read_inf_file(inf_path):
    """Read an .inf file trying multiple encodings for robustness."""
    for encoding in ('utf-8-sig', 'utf-8', 'cp1252', 'latin-1'):
        try:
            return inf_path.read_text(encoding=encoding)
        except (UnicodeDecodeError, UnicodeError):
            continue
    # Last resort: read with errors ignored
    return inf_path.read_text(encoding='utf-8', errors='ignore')


def parse_inf_mapping(inf_file):
    """Parse the [Strings] section of an .inf file into a cursor mapping dict."""
    inf_mapping = {}
    content = read_inf_file(inf_file)
    in_strings_section = False

    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith(';'):
            continue
        if line.startswith('[') and line.endswith(']'):
            in_strings_section = (line.lower() == '[strings]')
            continue

        if in_strings_section and '=' in line:
            key, val = line.split('=', 1)
            key = key.strip().lower()
            val = val.strip().strip('"').strip()

            stem = Path(val).stem.lower()
            if key in INF_TO_LINUX_MAP:
                inf_mapping[stem] = INF_TO_LINUX_MAP[key]

    return inf_mapping


def match_cursor_name(stem, mapping):
    """Match a cursor file stem against a name mapping dict.

    Prefers exact matches over substring matches. For substring matching,
    the longest (most specific) key wins.
    """
    # 1. Try exact match first
    if stem in mapping:
        return mapping[stem]

    # 2. Fallback to substring matching, longest key first
    sorted_keys = sorted(mapping.keys(), key=len, reverse=True)
    for key in sorted_keys:
        if key in stem:
            return mapping[key]

    return []


def sanitize_theme_name(name):
    """Sanitize a folder name into a safe theme name for Linux cursor themes."""
    return re.sub(r'[^a-zA-Z0-9_\-]', '_', name)


def main():
    if len(sys.argv) > 1:
        input_folder = sys.argv[1]
    else:
        input_folder = input("Please enter the path to the Windows cursor folder: ").strip()

    if not input_folder or not os.path.isdir(input_folder):
        print("Invalid folder path provided. Exiting.")
        return

    input_path = Path(input_folder)
    
    # Check if win2xcur is installed
    try:
        subprocess.run(["win2xcur", "--help"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        print("Error: 'win2xcur' is not installed or not in your PATH.")
        print("Please install it by running: pip install win2xcur")
        sys.exit(1)

    base_theme_name = sanitize_theme_name(input_path.name) + "_linux"
    output_path = input_path.parent / base_theme_name

    # If the folder already exists, append an incrementing number to avoid overwriting
    if output_path.exists():
        counter = 2
        while (input_path.parent / f"{base_theme_name}_{counter}").exists():
            counter += 1
        output_path = input_path.parent / f"{base_theme_name}_{counter}"

    theme_name = output_path.name
    cursors_dir = output_path / "cursors"

    print(f"\nOutput directory will be: {output_path}")

    # Create output directories
    cursors_dir.mkdir(parents=True, exist_ok=True)

    # Find all cursor files
    cursor_files = list(input_path.glob("*.cur")) + list(input_path.glob("*.ani"))
    
    if not cursor_files:
        print(f"No .cur or .ani files found in {input_folder}. Exiting.")
        return

    ani_count = sum(1 for f in cursor_files if f.suffix.lower() == '.ani')
    cur_count = sum(1 for f in cursor_files if f.suffix.lower() == '.cur')
    print(f"Found {len(cursor_files)} cursor files ({ani_count} .ani, {cur_count} .cur). Starting conversion...")

    # Convert each file individually so one broken file doesn't stop the rest
    converted_count = 0
    failed_count = 0
    for cursor_file in cursor_files:
        print(f"  Converting: {cursor_file.name}")
        try:
            result = subprocess.run(
                ["win2xcur", str(cursor_file), "-o", str(cursors_dir)],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                print(f"  ⚠ Warning: Failed to convert {cursor_file.name}.")
                print(f"    Error: {result.stderr.strip()}")
                failed_count += 1
            else:
                converted_count += 1
        except Exception as e:
            print(f"  ✗ Error running conversion on {cursor_file.name}: {e}")
            failed_count += 1
            continue

    # Look for an install.inf file to get precise mappings
    inf_mapping = {}
    inf_files = list(input_path.glob("*.inf"))
    if inf_files:
        inf_file = inf_files[0]
        print(f"\nFound install file: {inf_file.name}. Parsing it for exact mappings...")
        try:
            inf_mapping = parse_inf_mapping(inf_file)
        except Exception as e:
            print(f"Failed to parse {inf_file.name}: {e}. Falling back to fuzzy matching.")
            inf_mapping = {}

    # Map Windows names to Linux equivalents using symlinks
    print("\nMapping cursor names for Linux compatibility...")
    symlink_count = 0
    unmapped_files = []

    for generated_file in cursors_dir.iterdir():
        if not generated_file.is_file():
            continue
            
        stem = generated_file.stem.lower()
        
        linux_names_to_create = []
        
        # If we have inf mapping, use it first
        if inf_mapping and stem in inf_mapping:
            linux_names_to_create = inf_mapping[stem]
        else:
            # Fallback to name matching (exact first, then substring)
            linux_names_to_create = match_cursor_name(stem, WINDOWS_TO_LINUX_MAP)

        if not linux_names_to_create:
            unmapped_files.append(generated_file.name)

        # Create the matched symlinks
        for linux_name in linux_names_to_create:
            symlink_path = cursors_dir / linux_name
            # If this name doesn't exist yet, link it to the converted file
            if not symlink_path.exists():
                try:
                    # Create relative symlink for portability
                    symlink_path.symlink_to(generated_file.name)
                    symlink_count += 1
                except Exception as e:
                    print(f"  Could not create link {linux_name}: {e}")

    # Create secondary aliases for commonly needed cursor names
    # These point to existing cursor files/symlinks in the output
    for alias_name, targets in SECONDARY_ALIASES.items():
        alias_path = cursors_dir / alias_name
        if alias_path.exists():
            continue  # Already created by primary mapping
        # Find the first existing target to point to
        for target in targets:
            target_path = cursors_dir / target
            if target_path.exists():
                try:
                    # Resolve to the real file name for a clean symlink
                    real_name = target_path.resolve().name
                    alias_path.symlink_to(real_name)
                    symlink_count += 1
                except Exception as e:
                    print(f"  Could not create secondary alias {alias_name}: {e}")
                break

    # Create index.theme file required by Linux
    theme_content = f"""[Icon Theme]
Name={theme_name}
Comment=Converted from Windows Cursor Theme ({input_path.name})
Inherits=default
"""
    theme_file = output_path / "index.theme"
    theme_file.write_text(theme_content)

    # Print summary report
    print("\n" + "=" * 50)
    print("  Conversion complete!")
    print("=" * 50)
    print(f"  ✓ Converted:  {converted_count} cursor files ({ani_count} .ani, {cur_count} .cur)")
    if failed_count > 0:
        print(f"  ✗ Failed:     {failed_count} files")
    print(f"  ✓ Mapped:     {symlink_count} Linux symlinks created")
    if unmapped_files:
        print(f"  ⚠ Unmapped:   {len(unmapped_files)} files had no recognized name:")
        for name in unmapped_files:
            print(f"                  - {name}")
    print(f"  Output:       {output_path}")
    print()
    print("To use it, move the folder to ~/.local/share/icons/ or ~/.icons/")
    print("and select it in your Desktop Settings.")

if __name__ == "__main__":
    main()
