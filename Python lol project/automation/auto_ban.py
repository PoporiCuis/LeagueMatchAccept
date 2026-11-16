import json

CONFIG_FILE = "config.json"

#exe stuff???
from exe_stuff import get_config_path
#end of exe stuff

def auto_ban_once(session, base_url,detected_role):
    try:
        my_gameflow_phase = session.get(f"{base_url}/lol-champ-select/v1/session", verify=False, timeout=5)
        if my_gameflow_phase.status_code != 200:
            return False

        champ_data = my_gameflow_phase.json()
        phase = champ_data.get("timer", {}).get("phase", None)

        if phase != "BAN_PICK":
            return False

        with open(get_config_path(CONFIG_FILE), "r", encoding="utf-8") as f:
            config = json.load(f)

        #We assign ban_profile here
        if config.get("auto_detect_role", False) and detected_role:
            if detected_role in config.get("ban_priority_profiles", {}):
                config["last_ban_profile"] = detected_role
                with open(get_config_path(CONFIG_FILE), "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=4)
            ban_profile = detected_role
        else:
            ban_profile = config.get("last_ban_profile", "Custom")

        if not config.get("auto_ban", False):
            return False

        my_cell_id = champ_data.get("localPlayerCellId")
        if my_cell_id is None:
            return False

        ban_list = config.get("ban_priority_profiles", {}).get(ban_profile, [])

        if not ban_list:
            return False  # No champions to ban in selected profile

        for action_set in champ_data.get("actions", []):
            for action in action_set:
                if (
                    action.get("actorCellId") == my_cell_id and
                    action.get("type") == "ban" and
                    not action.get("completed", False) and
                    action.get("championId", -1) in [-1, 0]
                ):
                    for champ_id_to_ban in ban_list:
                        champ_id_to_ban = int(champ_id_to_ban)

                        res = session.patch(
                            f"{base_url}/lol-champ-select/v1/session/actions/{action.get('id')}",
                            json={"championId": champ_id_to_ban, "completed": True},
                            verify=False,
                            timeout=5,
                        )

                        if res.status_code == 204:
                            return True  # Successfully banned
                    return False  # Couldn't lock any champion
        return False

    except Exception:
        return False
