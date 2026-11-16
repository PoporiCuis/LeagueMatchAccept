# main_loop.py
import json
import threading
import time

import requests

from automation.auto_ban import auto_ban_once
from automation.auto_hover import auto_hover_once
from automation.auto_pick import auto_pick_once
from automation.auto_role import detect_role
from exe_stuff import get_config_path

CONFIG_FILE = "config.json"

RANKED_ROLE_MAP = {
    "top": "Top",
    "jungle": "Jungle",
    "middle": "Mid",
    "bottom": "ADC",
    "utility": "Support",
    "Custom": "Custom",
}


def start_monitor_loop(
    session,
    base_url,
    stop_thread,
    update_status,
    pick_ui,
    ban_ui,
    my_summoner_id,
    on_disconnect=None,
):
    def report_disconnect():
        if on_disconnect:
            on_disconnect()
        else:
            update_status("Connection lost to League Client")

    def monitor_loop():
        last_state = None
        hover_completed = False
        consecutive_connection_failures = 0

        while not stop_thread.is_set():
            try:
                try:
                    with open(get_config_path(), "r", encoding="utf-8") as config_file:
                        cfg = json.load(config_file)
                except FileNotFoundError:
                    cfg = {}

                try:
                    response = session.get(
                        f"{base_url}/lol-gameflow/v1/gameflow-phase",
                        verify=False,
                        timeout=5,
                    )
                    response.raise_for_status()
                    state = response.json()
                    consecutive_connection_failures = 0
                except (requests.RequestException, ValueError):
                    consecutive_connection_failures += 1
                    if consecutive_connection_failures >= 2:
                        report_disconnect()
                        return
                    update_status("League Client connection interrupted. Checking again…")
                    time.sleep(2)
                    continue

                last_ban_profile = cfg.get("last_ban_profile", "Custom")
                last_pick_profile = cfg.get("last_pick_profile", "Custom")

                if cfg.get("auto_detect_role", True):
                    ban_ui.update_ban_role_ui(last_ban_profile)
                    pick_ui.update_pick_role_ui(last_pick_profile)

                if state != last_state:
                    last_state = state
                    if state != "ChampSelect":
                        hover_completed = False

                if state == "Lobby":
                    update_status("Search for a match")
                elif state == "Matchmaking":
                    update_status("⌛ Searching for a match...")
                elif state == "ReadyCheck":
                    update_status("Match found! Accepting...")
                    if cfg.get("auto_accept", True):
                        session.post(
                            f"{base_url}/lol-matchmaking/v1/ready-check/accept",
                            verify=False,
                            timeout=5,
                        )
                        time.sleep(1)
                        update_status("✅ Match accepted!")
                elif state == "ChampSelect":
                    try:
                        session_data = session.get(
                            f"{base_url}/lol-champ-select/v1/session",
                            verify=False,
                            timeout=5,
                        )
                        if session_data.status_code == 200:
                            session_json = session_data.json()
                            phase = session_json.get("timer", {}).get("phase")

                            if cfg.get("auto_pick", False) and not hover_completed:
                                detected_role = cfg.get("last_pick_profile", "Custom")
                                if cfg.get("auto_detect_role", True):
                                    detected_role = detect_role(
                                        session_json,
                                        my_summoner_id,
                                        RANKED_ROLE_MAP,
                                        cfg.get("last_pick_profile", "Custom"),
                                    )
                                if auto_hover_once(session, base_url, detected_role):
                                    hover_completed = True

                            my_cell_id = session_json.get("localPlayerCellId")
                            actions = session_json.get("actions", [])
                            banning = False
                            picking = False

                            if cfg.get("auto_detect_role", True):
                                detected_role = detect_role(
                                    session_json,
                                    my_summoner_id,
                                    RANKED_ROLE_MAP,
                                    cfg.get("last_ban_profile", "Custom"),
                                )
                                if (
                                    cfg.get("last_ban_profile") != detected_role
                                    or cfg.get("last_pick_profile") != detected_role
                                ):
                                    cfg["last_ban_profile"] = detected_role
                                    cfg["last_pick_profile"] = detected_role
                                    with open(get_config_path(), "w", encoding="utf-8") as config_file:
                                        json.dump(cfg, config_file, indent=4)
                                    ban_ui.update_ban_role_ui(detected_role)
                                    pick_ui.update_pick_role_ui(detected_role)

                            if actions and my_cell_id is not None:
                                for action_set in actions:
                                    for action in action_set:
                                        if (
                                            action.get("actorCellId") == my_cell_id
                                            and action.get("isInProgress", False)
                                        ):
                                            if action.get("type") == "ban":
                                                banning = True
                                            elif action.get("type") == "pick":
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
                                elif cfg.get("auto_pick", False):
                                    update_status("💭 Showing champion intent...")
                                else:
                                    update_status("⏳ Waiting for your turn...")
                            elif phase == "FINALIZATION":
                                update_status("🔒 Finalizing selections...")
                            else:
                                update_status("Champion select in progress...")
                    except requests.RequestException:
                        consecutive_connection_failures += 1
                        if consecutive_connection_failures >= 2:
                            report_disconnect()
                            return
                        update_status("League Client connection interrupted. Checking again…")
                    except Exception as error:
                        update_status(f"Error fetching champ select phase: {error}")

                elif state == "InProgress":
                    update_status("In game... Disabling automation")
                else:
                    update_status(f"🧙 Welcome, {my_summoner_id}! Create or join a lobby")

            except requests.RequestException:
                consecutive_connection_failures += 1
                if consecutive_connection_failures >= 2:
                    report_disconnect()
                    return
                update_status("League Client connection interrupted. Checking again…")
                time.sleep(2)
                continue

            time.sleep(2)

    monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
    monitor_thread.start()
    return monitor_thread
