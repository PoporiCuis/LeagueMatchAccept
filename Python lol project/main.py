import json
import requests
import urllib3
from league_api.api_client import find_league_credentials
from gui.interface import start_gui
from lol_data.champion_data.champion_data import update_champion_data_if_needed, owned_champions

#exe thing
from exe_stuff import ensure_json_files, single_instance_check, get_config_path, resource_path
single_instance_check()
ensure_json_files()
#end exe stuff

# ---------- Config load/save ----------
def load_config():
    path = get_config_path()
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_config(data):
    path = get_config_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# ---------- League connection ----------
def connect_to_league():
    credentials = find_league_credentials()
    if not credentials:
        return None, None

    port = credentials['port']
    auth = credentials['auth']
    base_url = f"https://127.0.0.1:{port}"

    session = requests.Session()
    session.headers.update({
        "Authorization": f"Basic {auth}"
    })
    return session, base_url

def get_current_summoner_name(session, base_url):
    try:
        response = session.get(f"{base_url}/lol-summoner/v1/current-summoner", verify=False)
        if response.status_code == 200:
            data = response.json()
            game_name = data.get("gameName")
            if game_name:
                config = load_config()
                config["SummonerID"] = game_name
                save_config(config)
                print(f"SummonerID saved: {game_name}")
                return game_name
            else:
                print("Summoner name not found in JSON.")
        else:
            print("Failed to fetch summoner info. Status:", response.status_code)
    except Exception as e:
        print(f"Error getting summoner name: {e}")
    return None

# ---------- Main ----------
if __name__ == "__main__":
    urllib3.disable_warnings()
    config = load_config()
    session, base_url = connect_to_league()

    if session is None:
        print("❌ League Client not found. Launching UI with warning.")
        start_gui(None, None, client_connected=False)
    else:
        print("✅ Connected to League Client.")
        summoner_name = get_current_summoner_name(session, base_url)
        update_champion_data_if_needed()
        owned_champions()
        start_gui(session, base_url, client_connected=True)
