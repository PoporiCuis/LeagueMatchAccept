import threading
import pystray
from PIL import Image
from pystray import MenuItem as item

class TrayIcon(pystray.Icon):
    def __init__(self, tk_root, image, quit_callback):
        self.tk_root = tk_root
        self.quit_callback = quit_callback

        menu = pystray.Menu(
            item("Show", self.show_window),
            item("Quit", lambda icon, item: quit_callback(icon))
        )

        super().__init__(
            "LoL Match Assistant",
            image,
            menu=menu,
            default_action=self.on_left_click
        )

    def on_left_click(self, icon=None, item=None):
        """Handle left-click on tray icon"""
        print("Left-click detected on tray icon")
        self.show_window()

    def show_window(self, icon=None, item=None):
        """Show and restore the main window"""
        print("Tray icon clicked - showing window")  # Debug message
        try:
            # Force the window to show immediately
            self.tk_root.deiconify()
            self.tk_root.state('normal')
            self.tk_root.wm_state('normal')
            self.tk_root.lift()
            self.tk_root.attributes('-topmost', True)
            self.tk_root.update()
            self.tk_root.after(100, lambda: self.tk_root.attributes('-topmost', False))
            self.tk_root.focus_force()
            print("Window restored successfully")
        except Exception as e:
            print(f"Error restoring window: {e}")


    # Removed hide_window method since it's not needed

def start_tray(tk_root, image, quit_callback):
    """
    Start the tray icon in a daemon thread. Returns the icon instance.
    """
    icon = TrayIcon(tk_root, image, quit_callback)
    threading.Thread(target=icon.run, daemon=True).start()
    return icon
