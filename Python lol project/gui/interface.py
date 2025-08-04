import threading
import tkinter as tk
import time
import requests
import json

from client_state import is_idle
from champion_data import update_champion_data_if_needed
from auto_ban import auto_ban_once
from auto_pick import auto_pick_once

from gui.ban_list_ui import BanListUI
from gui.pick_list_ui import PickListUI

CONFIG_FILE = "config.json"


import os
import sys
def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)

import os
import sys

def get_config_path():
    # For dev: relative path
    if getattr(sys, 'frozen', False):
        # Running as bundled exe
        base_path = os.path.expanduser("~/.lolmatchassistant/")
        os.makedirs(base_path, exist_ok=True)
        return os.path.join(base_path, CONFIG_FILE)
    else:
        # Running in dev mode
        return os.path.join(os.path.abspath("."), CONFIG_FILE)




def start_gui(session, base_url, client_connected):
    root = tk.Tk()
    root.title("LoL Match Assistant")
    root.geometry("600x450")

    with open(resource_path(CONFIG_FILE), "r", encoding="utf-8") as f:

        config = json.load(f)

    status_var = tk.StringVar()
    status_label = tk.Label(root, textvariable=status_var, font=("Arial", 12))
    status_label.pack(pady=5)

    if not client_connected:
        status_var.set("❌ League Client not detected.\nPlease open the client and restart.")
        root.mainloop()
        return

    toggles_frame = tk.Frame(root)
    toggles_frame.pack(fill=tk.X, padx=10, pady=5)

    auto_ban_var = tk.BooleanVar(value=config.get("auto_ban", False))
    auto_pick_var = tk.BooleanVar(value=config.get("auto_pick", False))

    def save_toggle_config():
        try:
            with open(resource_path(CONFIG_FILE), "r", encoding="utf-8") as f:

                data = json.load(f)
        except Exception:
            data = {}

        data["auto_ban"] = auto_ban_var.get()
        data["auto_pick"] = auto_pick_var.get()

        with open(resource_path(CONFIG_FILE), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    auto_ban_cb = tk.Checkbutton(toggles_frame, text="Enable Auto Ban", variable=auto_ban_var, command=save_toggle_config)
    auto_ban_cb.pack(side=tk.LEFT, padx=10)

    auto_pick_cb = tk.Checkbutton(toggles_frame, text="Enable Auto Pick", variable=auto_pick_var, command=save_toggle_config)
    auto_pick_cb.pack(side=tk.LEFT, padx=10)

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

    def monitor_loop():
        last_state = None

        while not stop_thread.is_set():
            try:
                r = session.get(f"{base_url}/lol-gameflow/v1/gameflow-phase", verify=False, timeout=5)
                state = r.json()

                if state != last_state:
                    last_state = state

                if is_idle(state):
                    update_status("Search for a match")
                    time.sleep(5)
                    continue

                if state == "Matchmaking":
                    update_status("⌛ Searching for a match...")

                elif state == "ReadyCheck":
                    update_status("Match found! Accepting...")
                    with open(resource_path(CONFIG_FILE), "r", encoding="utf-8") as f:

                        cfg = json.load(f)
                    if cfg.get("auto_accept", True):
                        session.post(f"{base_url}/lol-matchmaking/v1/ready-check/accept", verify=False)
                        time.sleep(2)
                        update_status("✅ Match accepted!")

                elif state == "ChampSelect":
                    try:
                     
                        champ_data = session.get(f"{base_url}/lol-champ-select/v1/session", verify=False, timeout=5)
                        if champ_data.status_code == 200:
                            champ_json = champ_data.json()
                            phase = champ_json.get("timer", {}).get("phase", None)

                            my_cell_id = champ_json.get("localPlayerCellId", None)
                            if my_cell_id is not None:

                                actions = champ_json.get("actions", [])
                                banning = False
                                picking = False

                                if actions:
                                    for i, action_set in enumerate(actions):
                                        for action in action_set:
                                            actor_id = action.get("actorCellId", None)
                                            in_progress = action.get("isInProgress", False)
                                            action_type = action.get("type", "unknown")

                                            if actor_id == my_cell_id and in_progress:
                                                # Detect ban or pick
                                                if action_type == "ban":
                                                    banning = True
                                                elif action_type == "pick":
                                                    picking = True
                         
                                # Handle phase and action type combined
                                if phase == "BAN_PICK":
                                    if banning:
                                        update_status("🚫 Ban Phase: waiting to ban...")
                                        auto_ban_once(session, base_url)
                                    elif picking:
                                        update_status("✅ Pick Phase: preparing to pick...")
                                        auto_pick_once(session, base_url)
                                    else:
                                        update_status("⏳ Waiting for your turn...")
                                elif phase == "FINALIZATION":
                                    update_status("🔒 Finalizing selections...")
                                else:
                                    update_status("Champion select in progress...")

                    except Exception as e:
                        update_status(f"Error fetching champ select phase: {e}")

                elif state == "InProgress":
                    update_status("In game... Disabling automation")

                else:
                    update_status(f"Client state: {state}, create or enter a lobby")

            except requests.RequestException:
                update_status("Connection lost to League Client")
                time.sleep(5)

            time.sleep(1)

    monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
    monitor_thread.start()

    def on_close():
        stop_thread.set()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()