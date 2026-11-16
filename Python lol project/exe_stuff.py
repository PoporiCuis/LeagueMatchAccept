import os
import sys
import shutil

CONFIG_FILES = ["config.json", "champions.json", "champions_owned.json"]

# ---------- Base folder ----------
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)  # next to the exe
else:
    BASE_DIR = os.path.abspath(".")

# ---------- Paths ----------
def get_file_path(filename):
    """Get full path for a file next to the exe or in dev mode."""
    return os.path.join(BASE_DIR, filename)

def get_config_path(filename="config.json"):
    return get_file_path(filename)

def resource_path(relative_path):
    """Get path to bundled resource in PyInstaller (_MEIPASS) or fallback to script folder."""
    if hasattr(sys, "_MEIPASS"):  # only exists inside a PyInstaller exe
        return os.path.join(sys._MEIPASS, relative_path) # type: ignore
    return os.path.join(os.path.abspath("."), relative_path)


# ---------- Ensure JSON files exist ----------
def ensure_json_files():
    """Copy JSON files from resources to the exe folder if they don't exist."""
    for filename in CONFIG_FILES:
        dest = get_file_path(filename)
        if not os.path.exists(dest):
            src = resource_path(filename)
            if os.path.exists(src):
                shutil.copyfile(src, dest)
                print(f"✅ Copied {filename} to {dest}")
            else:
                print(f"⚠️ Resource {filename} not found in {src}, please copy manually.")

# ---------- Single-instance check ----------
def single_instance_check():
    import msvcrt
    import tkinter as tk
    from tkinter import messagebox
    import psutil

    # Use a more specific lock file name to avoid conflicts
    lock_file = os.path.join(BASE_DIR, "lol_match_assistant.lock")

    try:
        # Try to open and lock the file
        lock = open(lock_file, 'w')
        msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)

        # Write our PID to the lock file for identification
        lock.write(str(os.getpid()))
        lock.flush()

        # If we get here, we successfully acquired the lock
        # Store the lock handle globally so it doesn't get garbage collected
        global _app_lock
        _app_lock = lock

    except (OSError, IOError):
        # Check if there's actually a running process
        running_process = None
        if os.path.exists(lock_file):
            try:
                with open(lock_file, 'r') as f:
                    old_pid = int(f.read().strip())
                # Check if process is still running
                if psutil.pid_exists(old_pid):
                    proc = psutil.Process(old_pid)
                    if proc.is_running():
                        running_process = proc
            except (ValueError, psutil.NoSuchProcess, PermissionError):
                pass

        # Show message box with option to kill orphaned process
        root = tk.Tk()
        root.withdraw()  # Hide the main window

        if running_process:
            result = messagebox.askyesno(
                "LoL Match Assistant",
                "Another instance of LoL Match Assistant is already running.\n\n"
                "Would you like to close the existing instance and continue?"
            )

            if result:
                try:
                    running_process.terminate()
                    running_process.wait(timeout=5)
                    # Remove the lock file
                    if os.path.exists(lock_file):
                        os.remove(lock_file)
                    root.destroy()
                    # Retry the lock
                    return single_instance_check()
                except (psutil.TimeoutExpired, psutil.AccessDenied):
                    messagebox.showerror(
                        "Error",
                        "Could not close the existing instance. Please close it manually."
                    )
        else:
            # No running process found, just clean up the lock file
            if os.path.exists(lock_file):
                try:
                    os.remove(lock_file)
                    root.destroy()
                    return single_instance_check()
                except OSError:
                    pass

            messagebox.showwarning(
                "LoL Match Assistant",
                "Another instance appears to be running.\n\n"
                "Please check your system tray or task manager."
            )

        root.destroy()
        sys.exit(0)

# Global variable to keep the lock file handle alive
_app_lock = None
