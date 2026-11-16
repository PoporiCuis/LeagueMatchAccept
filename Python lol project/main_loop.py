# main_loop.py
import threading
import time
import json
import requests

from automation.auto_role import detect_role
from automation.auto_ban import auto_ban_once
from automation.auto_pick import auto_pick_once
from automation.auto_hover import auto_hover_once

CONFIG_FILE = "config.json"

RANKED_ROLE_MAP = {
    "top": "Top",
    "jungle": "Jungle",
    "middle": "Mid",
    "bottom": "ADC",
    "utility": "Support",
    "Custom": "Custom"
}

# ---------- EXE stuff ----------
from exe_stuff import get_file_path, get_config_path, resource_path

# Optional: load champions_owned.json just for reference
# Removed problematic file load at import time

# ---------- End EXE stuff ----------

def start_monitor_loop(session, base_url, stop_thread, update_status, pick_ui, ban_ui, my_summoner_id):

    def monitor_loop(session, base_url, stop_thread, update_status, pick_ui, ban_ui, my_summoner_id):
        last_state = None
        hover_completed = False  # Track if we've already hovered this champion select

        while not stop_thread.is_set():
            try:
                # ---------- Load config ----------
                try:
                    with open(get_config_path(), "r", encoding="utf-8") as f:
                        cfg = json.load(f)
                except FileNotFoundError:
                    cfg = {}

                # ---------- Fetch current gameflow phase ----------
                try:
                    response = session.get(f"{base_url}/lol-gameflow/v1/gameflow-phase", verify=False, timeout=5)
                    state = response.json()
                except requests.RequestException:
                    update_status("Connection lost to League Client")
                    time.sleep(5)
                    continue

                last_ban_profile = cfg.get("last_ban_profile", "Custom")
                last_pick_profile = cfg.get("last_pick_profile", "Custom")

                # Update UI role indicators if role detection enabled
                if cfg.get("auto_detect_role", True):
                    ban_ui.update_ban_role_ui(last_ban_profile)
                    pick_ui.update_pick_role_ui(last_pick_profile)

                # ---------- State handling ----------
                if state != last_state:
                    last_state = state
                    # Reset hover state when leaving champion select
                    if last_state != "ChampSelect":
                        hover_completed = False

                if state == "Lobby":
                    update_status("Search for a match")
                elif state == "Matchmaking":
                    update_status("⌛ Searching for a match...")
                elif state == "ReadyCheck":
                    update_status("Match found! Accepting...")
                    if cfg.get("auto_accept", True):
                        session.post(f"{base_url}/lol-matchmaking/v1/ready-check/accept", verify=False)
                        time.sleep(1)
                        update_status("✅ Match accepted!")
                elif state == "ChampSelect":
                    try:
                        session_data = session.get(f"{base_url}/lol-champ-select/v1/session", verify=False, timeout=5)
                        if session_data.status_code == 200:
                            session_json = session_data.json()

                            phase = session_json.get("timer", {}).get("phase")

                            # Auto hover when auto_pick is enabled (integrated functionality)
                            if cfg.get("auto_pick", False) and not hover_completed:
                                detected_role = cfg.get("last_pick_profile", "Custom")
                                if cfg.get("auto_detect_role", True):
                                    detected_role = detect_role(
                                        session_json,
                                        my_summoner_id,
                                        RANKED_ROLE_MAP,
                                        cfg.get("last_pick_profile", "Custom")
                                    )
                                hover_success = auto_hover_once(session, base_url, detected_role)
                                if hover_success:
                                    hover_completed = True
                            my_cell_id = session_json.get("localPlayerCellId")

                            actions = session_json.get("actions", [])
                            banning = picking = False

                            if cfg.get("auto_detect_role", True):
                                detected_role = detect_role(
                                    session_json,
                                    my_summoner_id,
                                    RANKED_ROLE_MAP,
                                    cfg.get("last_ban_profile", "Custom")
                                )
                                if (cfg.get("last_ban_profile") != detected_role or
                                    cfg.get("last_pick_profile") != detected_role):
                                    cfg["last_ban_profile"] = detected_role
                                    cfg["last_pick_profile"] = detected_role
                                    with open(get_config_path(), "w", encoding="utf-8") as f:
                                        json.dump(cfg, f, indent=4)
                                    ban_ui.update_ban_role_ui(detected_role)
                                    pick_ui.update_pick_role_ui(detected_role)

                            if actions and my_cell_id is not None:
                                for action_set in actions:
                                    for action in action_set:
                                        actor_id = action.get("actorCellId")
                                        in_progress = action.get("isInProgress", False)
                                        action_type = action.get("type", "unknown")

                                        if actor_id == my_cell_id and in_progress:
                                            if action_type == "ban":
                                                banning = True
                                            elif action_type == "pick":
                                                picking = True

                            if phase == "BAN_PICK":
                                if banning:
                                    update_status("🚫 Ban Phase: waiting to ban...")
                                    if cfg.get("auto_ban", True):
                                        auto_ban_once(session, base_url, last_ban_profile)
                                elif picking:
                                    update_status("✅ Pick Phase: preparing to pick...")
                                    if cfg.get("auto_pick", True):
                                        auto_pick_once(session, base_url, last_pick_profile)
                                else:
                                    if cfg.get("auto_pick", False):
                                        update_status("💭 Showing champion intent...")
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
                    update_status(f"🧙 Welcome, {my_summoner_id}! Create or join a lobby")

            except requests.RequestException:
                update_status("Connection lost to League Client")
                time.sleep(5)

            time.sleep(2)

    monitor_thread = threading.Thread(
        target=monitor_loop,
        args=(session, base_url, stop_thread, update_status, pick_ui, ban_ui, my_summoner_id),
        daemon=True
    )
    monitor_thread.start()
    return monitor_thread
