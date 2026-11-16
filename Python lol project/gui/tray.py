import threading
import tkinter as tk

import pystray
from pystray import MenuItem as item


class TrayIcon(pystray.Icon):
    def __init__(self, tk_root, image, quit_callback):
        self.tk_root = tk_root

        menu = pystray.Menu(
            item("Show", self.show_window, default=True),
            item("Quit", lambda icon, menu_item: quit_callback(icon)),
        )

        super().__init__("LoL Match Assistant", image, menu=menu)

    def show_window(self, icon=None, menu_item=None):
        """Restore the Tk window on its own event loop."""
        try:
            self.tk_root.after(0, self._restore_window)
        except tk.TclError:
            pass

    def _restore_window(self):
        try:
            if not self.tk_root.winfo_exists():
                return
            self.tk_root.deiconify()
            self.tk_root.state("normal")
            self.tk_root.lift()
            self.tk_root.attributes("-topmost", True)
            self.tk_root.after(
                100,
                lambda: self.tk_root.attributes("-topmost", False),
            )
            self.tk_root.focus_force()
        except tk.TclError:
            pass


def start_tray(tk_root, image, quit_callback):
    """Start the tray icon in a daemon thread and return it."""
    icon = TrayIcon(tk_root, image, quit_callback)
    threading.Thread(target=icon.run, daemon=True).start()
    return icon
