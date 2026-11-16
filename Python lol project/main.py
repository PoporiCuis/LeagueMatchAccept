import json
import urllib3

from exe_stuff import ensure_json_files, get_config_path, single_instance_check
from gui.interface import start_gui
from league_api.api_client import connect_to_league
from lol_data.champion_data.champion_data import (
    owned_champions,
    update_champion_data_if_needed,
)

single_instance_check()
ensure_json_files()


def load_config():
    with open(get_config_path(), "r", encoding="utf-8") as config_file:
        return json.load(config_file)


def save_config(data):
    with open(get_config_path(), "w", encoding="utf-8") as config_file:
        json.dump(data, config_file, indent=4)


def get_current_summoner_name(session, base_url):
    try:
        response = session.get(
            f"{base_url}/lol-summoner/v1/current-summoner",
            verify=False,
            timeout=5,
        )
        if response.status_code != 200:
            print("Failed to fetch summoner info. Status:", response.status_code)
            return None

        game_name = response.json().get("gameName")
        if not game_name:
            print("Summoner name not found in JSON.")
            return None

        config = load_config()
        config["SummonerID"] = game_name
        save_config(config)
        print(f"SummonerID saved: {game_name}")
        return game_name
    except Exception as error:
        print(f"Error getting summoner name: {error}")
        return None


def prepare_connected_session(session, base_url):
    """Refresh local client data after a new League connection is found."""
    summoner_name = get_current_summoner_name(session, base_url)
    update_champion_data_if_needed()
    owned_champions(session, base_url)
    return summoner_name


if __name__ == "__main__":
    urllib3.disable_warnings()
    session, base_url = connect_to_league()

    if session is None:
        print("League Client not found. The app will retry automatically.")
        start_gui(
            None,
            None,
            client_connected=False,
            on_connected=prepare_connected_session,
        )
    else:
        print("Connected to League Client.")
        summoner_name = prepare_connected_session(session, base_url)
        start_gui(
            session,
            base_url,
            client_connected=True,
            on_connected=prepare_connected_session,
            summoner_id=summoner_name,
        )
