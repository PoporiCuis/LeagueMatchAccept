import json
import requests

CONFIG_FILE = "config.json"

#exe stuff
from exe_stuff import get_file_path, get_config_path, resource_path
#end of exe stuff

def auto_hover_once(session, base_url, current_role):
    """
    Hover the first champion from the pick priority list to show intent to teammates.
    This is integrated with auto_pick functionality.
    """
    try:
        # Load config to get pick priorities
        with open(get_config_path(CONFIG_FILE), "r", encoding="utf-8") as f:
            config = json.load(f)

        # Check if auto_pick is enabled (we use same toggle)
        if not config.get("auto_pick", False):
            return False

        # Determine which profile to use
        if config.get("auto_detect_role", False) and current_role:
            if current_role in config.get("pick_priority_profiles", {}):
                hover_profile = current_role
            else:
                hover_profile = config.get("last_pick_profile", "Custom")
        else:
            hover_profile = config.get("last_pick_profile", "Custom")

        # Get the pick priority list for this role
        pick_priority = config.get("pick_priority_profiles", {}).get(hover_profile, [])

        if not pick_priority:
            return False  # No champions to hover

        # Get the first champion from the list as hover intent
        hover_champion_id = int(pick_priority[0])

        # Get current champion select session
        resp = session.get(f"{base_url}/lol-champ-select/v1/session", verify=False, timeout=5)
        if resp.status_code != 200:
            return False

        session_data = resp.json()
        my_cell_id = session_data.get("localPlayerCellId")

        if my_cell_id is None:
            return False

        # Check if we already have this champion as pick intent
        my_team = session_data.get("myTeam", [])
        for player in my_team:
            if player.get("cellId") == my_cell_id:
                current_intent = player.get("championPickIntent", 0)
                if current_intent == hover_champion_id:
                    return True  # Already hovering the right champion
                break

        # Try different hover approaches
        hover_url = f"{base_url}/lol-champ-select/v1/session/my-selection"

        # Method 1: Try with championPickIntent only
        hover_resp = session.patch(
            hover_url,
            json={"championPickIntent": hover_champion_id},
            verify=False
        )

        # Method 2: Try with both championId and championPickIntent (some patches need both)
        if hover_resp.status_code == 204:
            hover_resp2 = session.patch(
                hover_url,
                json={
                    "championId": hover_champion_id,
                    "championPickIntent": hover_champion_id
                },
                verify=False
            )

        # Method 3: Try the actions endpoint approach (like ban/pick)
        try:
            session_check = session.get(f"{base_url}/lol-champ-select/v1/session", verify=False, timeout=5)
            if session_check.status_code == 200:
                session_data_check = session_check.json()
                actions = session_data_check.get("actions", [])

                # Look for any incomplete pick action for our cell
                for action_set in actions:
                    for action in action_set:
                        if (action.get("actorCellId") == my_cell_id and
                            action.get("type") == "pick" and
                            not action.get("completed", False)):

                            # Try setting championId without completing the action
                            action_url = f"{base_url}/lol-champ-select/v1/session/actions/{action.get('id')}"
                            action_resp = session.patch(
                                action_url,
                                json={"championId": hover_champion_id, "completed": False},
                                verify=False
                            )
                            break
        except Exception as e:
            pass

        # Verify if hover worked by checking session again
        verify_resp = session.get(f"{base_url}/lol-champ-select/v1/session", verify=False, timeout=5)
        if verify_resp.status_code == 200:
            verify_data = verify_resp.json()
            my_team_verify = verify_data.get("myTeam", [])
            for player in my_team_verify:
                if player.get("cellId") == my_cell_id:
                    final_intent = player.get("championPickIntent", 0)
                    final_champ = player.get("championId", 0)
                    return final_intent == hover_champion_id or final_champ == hover_champion_id

        return hover_resp.status_code == 204

    except Exception as e:
        return False
