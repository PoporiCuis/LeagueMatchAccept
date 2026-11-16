import threading
import tkinter as tk
import json
import os
import sys
from PIL import Image

from gui import tray  # tray.py module
from lol_data.champion_data.champion_data import update_champion_data_if_needed
from gui.ban_list_ui import BanListUI
from gui.pick_list_ui import PickListUI
from main_loop import start_monitor_loop

CONFIG_FILE = "config.json"

#exe stuff???
from exe_stuff import get_file_path, get_config_path, resource_path
# Remove problematic file load at import time
#end of exe stuff

def create_tray_image():
    # Load your actual .ico file
    ico_path = resource_path("minion.ico")
    return Image.open(ico_path)

def start_gui(session, base_url, client_connected):
    root = tk.Tk()
    root.title("LoL Match Assistant")
    root.geometry("600x450")

    with open(get_config_path(CONFIG_FILE), "r", encoding="utf-8") as f:
        config = json.load(f)

    status_var = tk.StringVar()
    status_label = tk.Label(root, textvariable=status_var, font=("Arial", 12))
    status_label.pack(pady=5)
    my_summoner_id = config.get("SummonerID")

    if not client_connected:
        status_var.set("❌ League Client not detected.\nPlease open the client and restart.")
        root.mainloop()
        return

    # --- Toggles ---
    toggles_frame = tk.Frame(root)
    toggles_frame.pack(fill=tk.X, padx=10, pady=5)

    auto_accept_var = tk.BooleanVar(value=config.get("auto_accept", False))
    auto_ban_var = tk.BooleanVar(value=config.get("auto_ban", False))
    auto_pick_var = tk.BooleanVar(value=config.get("auto_pick", False))
    role_detect_var = tk.BooleanVar(value=config.get("auto_detect_role", False))

    def save_toggle_config():
        try:
            with open(get_config_path(CONFIG_FILE), "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}

        data["auto_accept"] = auto_accept_var.get()
        data["auto_ban"] = auto_ban_var.get()
        data["auto_pick"] = auto_pick_var.get()
        data["auto_detect_role"] = role_detect_var.get()

        with open(get_config_path(CONFIG_FILE), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    tk.Checkbutton(toggles_frame, text="Enable Auto Accept", variable=auto_accept_var,
                   command=save_toggle_config).pack(side=tk.LEFT, padx=10)
    tk.Checkbutton(toggles_frame, text="Enable Auto Ban", variable=auto_ban_var,
                   command=save_toggle_config).pack(side=tk.LEFT, padx=10)
    tk.Checkbutton(toggles_frame, text="Enable Auto Pick", variable=auto_pick_var,
                   command=save_toggle_config).pack(side=tk.LEFT, padx=10)
    tk.Checkbutton(toggles_frame, text="Enable Role Detection", variable=role_detect_var,
                   command=save_toggle_config).pack(side=tk.LEFT, padx=10)


    # --- Lists ---
    lists_frame = tk.Frame(root)
    lists_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    ban_ui = BanListUI(lists_frame)
    ban_ui.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

    pick_ui = PickListUI(lists_frame)
    pick_ui.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

    stop_thread = threading.Event()
    update_champion_data_if_needed()

    def update_status(text):
        status_var.set(text)
        root.update_idletasks()

    start_monitor_loop(session, base_url, stop_thread, update_status,
                       pick_ui, ban_ui, my_summoner_id)

    # --- Tray setup ---
    def quit_app(icon):
        stop_thread.set()
        icon.stop()
        root.after(0, root.destroy)

    icon_image = create_tray_image()
    icon = tray.start_tray(root, icon_image, quit_app)

    def on_close():
        # Hide window instead of destroying
        root.withdraw()
        # Tray icon already running, do NOT start again

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()
