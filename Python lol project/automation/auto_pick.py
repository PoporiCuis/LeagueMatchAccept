import json
import os
import sys

CONFIG_FILE = "config.json"

#exe stuff
from exe_stuff import get_file_path, get_config_path, resource_path
#end of exe stuff

def auto_pick_once(session, base_url,current_role):

    try:
        with open(get_config_path(CONFIG_FILE), "r", encoding="utf-8") as f:
            config = json.load(f)

        #we catch any missmatch so if autodetect is ON we do detect
        if config.get("auto_detect_role", False) and current_role:
            if current_role in config.get("pick_priority_profiles", {}):
                if config.get("last_pick_profile") != current_role:
                    config["last_pick_profile"] = current_role
                    with open(get_config_path(CONFIG_FILE), "w", encoding="utf-8") as f:
                        json.dump(config, f, indent=4)
            pick_profile = current_role
        else:
            pick_profile = config.get("last_pick_profile", "Custom")

        # NEW: Get current pick profile and list
        pick_priority = config.get("pick_priority_profiles", {}).get(pick_profile, [])

        if not pick_priority:
            return False

        resp = session.get(f"{base_url}/lol-champ-select/v1/session", verify=False, timeout=5)
        if resp.status_code != 200:
            return False

        session_data = resp.json()

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
        # BUT exclude our own pick intent (hover) from being considered "taken"
        taken_champions = set()
        for phase_actions in actions:
            if isinstance(phase_actions, list):
                for action in phase_actions:
                    champ_id = action.get("championId", 0)
                    if champ_id != 0:
                        # Don't consider our own pick action as "taken" since we can still complete it
                        if action.get("actorCellId") == my_cell_id and action.get("type") == "pick":
                            continue  # Skip our own pick action
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