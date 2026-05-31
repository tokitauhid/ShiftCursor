import os
import sys
import subprocess
import shutil
from pathlib import Path

# Common mapping from Windows cursor filenames (without extension) to Linux X11 names
WINDOWS_TO_LINUX_MAP = {
    "arrow": ["left_ptr", "default", "arrow"],
    "help": ["help", "question_arrow"],
    "appstarting": ["left_ptr_watch", "half-busy"],
    "wait": ["watch", "wait", "busy"],
    "cross": ["cross", "crosshair", "cross_reverse"],
    "ibeam": ["xterm", "text", "ibeam"],
    "nwpen": ["pencil", "draft"],
    "no": ["crossed_circle", "not-allowed", "circle"],
    "sizens": ["sb_v_double_arrow", "size_ver", "n-resize", "s-resize", "ns-resize"],
    "sizewe": ["sb_h_double_arrow", "size_hor", "e-resize", "w-resize", "ew-resize"],
    "sizenwse": ["size_fdiag", "nw-resize", "se-resize", "nwse-resize"],
    "sizenesw": ["size_bdiag", "ne-resize", "sw-resize", "nesw-resize"],
    "sizeall": ["fleur", "size_all", "move"],
    "uparrow": ["up_arrow", "center_ptr"],
    "hand": ["pointer", "hand", "hand2", "link"],
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

    theme_name = f"{input_path.name}_linux"
    output_path = input_path.parent / theme_name
    cursors_dir = output_path / "cursors"

    print(f"\nOutput directory will be: {output_path}")

    # Create output directories
    if output_path.exists():
        print(f"Directory '{output_path.name}' already exists. Cleaning it up...")
        shutil.rmtree(output_path)
    
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

    # Map Windows names to Linux equivalents using symlinks
    print("\nMapping cursor names for Linux compatibility...")
    for generated_file in cursors_dir.iterdir():
        if not generated_file.is_file():
            continue
            
        base_name = generated_file.name.lower()
        
        # Check if the generated file's original name matches any of our known windows names
        for win_name, linux_names in WINDOWS_TO_LINUX_MAP.items():
            if win_name in base_name:
                for linux_name in linux_names:
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
