import json
import time
import os
import sys

CONFIG_FILE = "config.json"

def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)

def auto_pick_once(session, base_url):
    try:
        with open(resource_path(CONFIG_FILE), "r", encoding="utf-8") as f:
            config = json.load(f)

        if not config.get("auto_pick", False):
            return False

        pick_priority = config.get("pick_priority", [])
        if not pick_priority:
            return False

        resp = session.get(f"{base_url}/lol-champ-select/v1/session", verify=False, timeout=5)
        if resp.status_code != 200:
            return False

        session_data = resp.json()
        phase = session_data.get("timer", {}).get("phase", "")

        if phase not in ("BAN_PICK", "PICK_PHASE"):
            return False

        my_cell_id = session_data.get("localPlayerCellId")
        if my_cell_id is None:
            return False

        # Find your next pick action
        my_pick_action = None
        actions = session_data.get("actions", [])
        for phase_actions in actions:
            if not isinstance(phase_actions, list):
                continue
            for action in phase_actions:
                if (
                    action.get("actorCellId") == my_cell_id and
                    action.get("type") == "pick" and
                    not action.get("completed", False)
                ):
                    my_pick_action = action
                    break
            if my_pick_action:
                break

        if my_pick_action is None:
            return False

        # Collect banned/picked champion IDs to avoid duplicates
        taken_champions = set()
        for phase_actions in actions:
            if isinstance(phase_actions, list):
                for action in phase_actions:
                    champ_id = action.get("championId", 0)
                    if champ_id != 0:
                        taken_champions.add(champ_id)

        # Try picks from priority list
        for champ_str in pick_priority:
            champ_id = int(champ_str)
            if champ_id in taken_champions:
                continue

            pick_url = f"{base_url}/lol-champ-select/v1/session/actions/{my_pick_action['id']}"
            patch_resp = session.patch(
                pick_url,
                json={
                    "championId": champ_id,
                    "completed": True
                },
                verify=False
            )

            if patch_resp.status_code == 204:
                return True  # Successfully picked and locked in

        return False

    except Exception:
        return False
