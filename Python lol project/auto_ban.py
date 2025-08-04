import time
import json
import os
import sys

CONFIG_FILE = "config.json"

def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)

def auto_ban_once(session, base_url):
    try:
        r = session.get(f"{base_url}/lol-champ-select/v1/session", verify=False, timeout=5)
        if r.status_code != 200:
            return False

        champ_data = r.json()
        phase = champ_data.get("timer", {}).get("phase", None)

        if phase != "BAN_PICK":
            return False

        with open(resource_path(CONFIG_FILE), "r", encoding="utf-8") as f:
            config = json.load(f)

        if not config.get("auto_ban", False):
            return False

        my_cell_id = champ_data.get("localPlayerCellId")
        if my_cell_id is None:
            return False

        for action_set in champ_data.get("actions", []):
            for action in action_set:
                if (
                    action.get("actorCellId") == my_cell_id and
                    action.get("type") == "ban" and
                    not action.get("completed", False) and
                    action.get("championId", -1) in [-1, 0]
                ):
                    for champ_id_to_ban in config.get("ban_priority", []):
                        champ_id_to_ban = int(champ_id_to_ban)

                        res = session.patch(
                            f"{base_url}/lol-champ-select/v1/session/actions/{action.get('id')}",
                            json={"championId": champ_id_to_ban, "completed": True},
                            verify=False
                        )

                        if res.status_code == 204:
                            return True  # Successfully banned
                    return False  # Couldn't lock any champion
        return False

    except Exception:
        return False
