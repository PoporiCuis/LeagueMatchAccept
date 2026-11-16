import os
import shutil
import sys

CONFIG_FILES = ["config.json", "champions.json"]

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def get_file_path(filename):
    """Get the path to a file beside the app or executable."""
    return os.path.join(BASE_DIR, filename)


def get_config_path(filename="config.json"):
    return get_file_path(filename)


def resource_path(relative_path):
    """Find a bundled resource or a file beside the source code."""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(BASE_DIR, relative_path)


def ensure_json_files():
    """Copy packaged JSON defaults beside the executable when needed."""
    for filename in CONFIG_FILES:
        destination = get_file_path(filename)
        if not os.path.exists(destination):
            resource_name = "config.default.json" if filename == "config.json" else filename
            source = resource_path(resource_name)
            if os.path.exists(source):
                shutil.copyfile(source, destination)
                print(f"✅ Copied {filename} to {destination}")
            else:
                print(f"⚠️ Resource {filename} not found in {source}.")


def acquire_instance_lock():
    """Return an open lock file, or None when another instance owns it."""
    import msvcrt

    lock_path = get_file_path("lol_match_assistant.lock")
    lock_file = open(lock_path, "a+")

    try:
        lock_file.seek(0, os.SEEK_END)
        if lock_file.tell() == 0:
            lock_file.write("\0")
            lock_file.flush()

        lock_file.seek(0)
        msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        lock_file.close()
        return None

    try:
        lock_file.seek(0)
        lock_file.truncate()
        lock_file.write(str(os.getpid()))
        lock_file.flush()
    except OSError:
        lock_file.close()
        return None

    return lock_file


def single_instance_check():
    import tkinter as tk
    from tkinter import messagebox

    lock_file = acquire_instance_lock()
    if lock_file is None:
        root = tk.Tk()
        root.withdraw()
        messagebox.showwarning(
            "LoL Match Assistant",
            "LoL Match Assistant is already running.\n\n"
            "Check the system tray for the open app.",
        )
        root.destroy()
        sys.exit(0)

    # Keep the file handle alive so Windows keeps the lock for this process.
    global _app_lock
    _app_lock = lock_file


_app_lock = None
