import os
import sys
import subprocess
import shutil
from pathlib import Path

# Common mapping from Windows cursor filenames (without extension) to Linux X11 names
WINDOWS_TO_LINUX_MAP = {
    "arrow": ["left_ptr", "default", "arrow"],
    "normal select": ["left_ptr", "default", "arrow"],
    "help": ["help", "question_arrow"],
    "help select": ["help", "question_arrow"],
    "appstarting": ["left_ptr_watch", "half-busy"],
    "working in background": ["left_ptr_watch", "half-busy"],
    "wait": ["watch", "wait", "busy"],
    "busy": ["watch", "wait", "busy"],
    "cross": ["cross", "crosshair", "cross_reverse"],
    "precision select": ["cross", "crosshair", "cross_reverse"],
    "ibeam": ["xterm", "text", "ibeam"],
    "text select": ["xterm", "text", "ibeam"],
    "nwpen": ["pencil", "draft"],
    "handwriting": ["pencil", "draft"],
    "no": ["crossed_circle", "not-allowed", "circle"],
    "unavailable": ["crossed_circle", "not-allowed", "circle"],
    "sizens": ["sb_v_double_arrow", "size_ver", "n-resize", "s-resize", "ns-resize"],
    "vertical resize": ["sb_v_double_arrow", "size_ver", "n-resize", "s-resize", "ns-resize"],
    "sizewe": ["sb_h_double_arrow", "size_hor", "e-resize", "w-resize", "ew-resize"],
    "horizontal resize": ["sb_h_double_arrow", "size_hor", "e-resize", "w-resize", "ew-resize"],
    "sizenwse": ["size_fdiag", "nw-resize", "se-resize", "nwse-resize"],
    "diagonal resize 1": ["size_fdiag", "nw-resize", "se-resize", "nwse-resize"],
    "sizenesw": ["size_bdiag", "ne-resize", "sw-resize", "nesw-resize"],
    "diagonal resize 2": ["size_bdiag", "ne-resize", "sw-resize", "nesw-resize"],
    "sizeall": ["fleur", "size_all", "move"],
    "move": ["fleur", "size_all", "move"],
    "uparrow": ["up_arrow", "center_ptr"],
    "alternate select": ["up_arrow", "center_ptr"],
    "hand": ["pointer", "hand", "hand2", "link"],
    "link": ["pointer", "hand", "hand2", "link"],
    "link select": ["pointer", "hand", "hand2", "link"],
    "pin": ["pin", "alias"],
    "person": ["person", "dnd-ask"]
}

# Mapping from Windows .inf file variables to Linux X11 names
INF_TO_LINUX_MAP = {
    "pointer": ["left_ptr", "default", "arrow"],
    "help": ["help", "question_arrow"],
    "work": ["left_ptr_watch", "half-busy"],
    "busy": ["watch", "wait", "busy"],
    "cross": ["cross", "crosshair", "cross_reverse"],
    "text": ["xterm", "text", "ibeam"],
    "hand": ["pencil", "draft"],  # 'hand' in .inf is handwriting
    "unavailiable": ["crossed_circle", "not-allowed", "circle"], # common typo in .inf
    "unavailable": ["crossed_circle", "not-allowed", "circle"],
    "vert": ["sb_v_double_arrow", "size_ver", "n-resize", "s-resize", "ns-resize"],
    "horz": ["sb_h_double_arrow", "size_hor", "e-resize", "w-resize", "ew-resize"],
    "dgn1": ["size_fdiag", "nw-resize", "se-resize", "nwse-resize"],
    "dgn2": ["size_bdiag", "ne-resize", "sw-resize", "nesw-resize"],
    "move": ["fleur", "size_all", "move"],
    "alternate": ["up_arrow", "center_ptr"],
    "link": ["pointer", "hand", "hand2", "link"],
    "pin": ["pin", "alias"],
    "person": ["person", "dnd-ask"]
}

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

    base_theme_name = f"{input_path.name}_linux"
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

    print(f"Found {len(cursor_files)} cursor files. Starting conversion...")

    # Convert each file individually so one broken file doesn't stop the rest
    for cursor_file in cursor_files:
        print(f"Converting: {cursor_file.name}")
        try:
            result = subprocess.run(
                ["win2xcur", str(cursor_file), "-o", str(cursors_dir)],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                print(f"Warning: Failed to convert {cursor_file.name}.")
                print(f"Error Details: {result.stderr.strip()}")
        except Exception as e:
            print(f"Error running conversion on {cursor_file.name}: {e}")
            continue

    # Look for an install.inf file to get precise mappings
    inf_mapping = {}
    inf_files = list(input_path.glob("*.inf"))
    if inf_files:
        inf_file = inf_files[0]
        print(f"Found install file: {inf_file.name}. Parsing it for exact mappings...")
        in_strings_section = False
        try:
            with open(inf_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
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
        except Exception as e:
            print(f"Failed to parse {inf_file.name}: {e}. Falling back to fuzzy matching.")
            inf_mapping = {}

    # Map Windows names to Linux equivalents using symlinks
    print("\nMapping cursor names for Linux compatibility...")
    for generated_file in cursors_dir.iterdir():
        if not generated_file.is_file():
            continue
            
        stem = generated_file.stem.lower()
        
        linux_names_to_create = []
        
        # If we have inf mapping, use it first
        if inf_mapping and stem in inf_mapping:
            linux_names_to_create = inf_mapping[stem]
        else:
            # Fallback to fuzzy substring matching
            # Sort keys by length descending to match the longest (most specific) name first
            sorted_win_names = sorted(WINDOWS_TO_LINUX_MAP.keys(), key=len, reverse=True)
            
            matched_win_name = None
            for win_name in sorted_win_names:
                if win_name in stem:
                    matched_win_name = win_name
                    break  # Found the most specific match for this file
                    
            if matched_win_name:
                linux_names_to_create = WINDOWS_TO_LINUX_MAP[matched_win_name]
                
        # Create the matched symlinks
        for linux_name in linux_names_to_create:
            symlink_path = cursors_dir / linux_name
            # If this name doesn't exist yet, link it to the converted file
            if not symlink_path.exists():
                try:
                    # Create relative symlink for portability
                    symlink_path.symlink_to(generated_file.name)
                except Exception as e:
                    print(f"Could not create link {linux_name}: {e}")

    # Create index.theme file required by Linux
    theme_content = f"""[Icon Theme]
Name={theme_name}
Comment=Converted from Windows Cursor Theme ({input_path.name})
"""
    theme_file = output_path / "index.theme"
    theme_file.write_text(theme_content)

    print("\nConversion complete!")
    print(f"Your Linux cursor theme is ready at: {output_path}")
    print("To use it, move the folder to ~/.local/share/icons/ or ~/.icons/ and select it in your Desktop Settings.")

if __name__ == "__main__":
    main()
