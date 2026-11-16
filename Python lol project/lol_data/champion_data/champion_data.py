import requests
import json
import os
import sys


CHAMPIONS_FILE = "champions.json"

#exe stuff???
from exe_stuff import get_file_path, get_config_path, resource_path
# Remove the problematic file load at import time
#end of exe stuff

def fetch_latest_patch():
    url = "https://ddragon.leagueoflegends.com/api/versions.json"
    r = requests.get(url)
    r.raise_for_status()
    return r.json()[0]  # latest patch

def fetch_champion_list():
    patch = fetch_latest_patch()
    url = f"https://ddragon.leagueoflegends.com/cdn/{patch}/data/en_US/champion.json"
    r = requests.get(url)
    r.raise_for_status()
    data = r.json()["data"]

    champ_dict = {}
    for champ_key in data:
        champ = data[champ_key]
        champ_id = int(champ["key"])
        champ_name = champ["name"]
        champ_dict[champ_id] = champ_name

    # Save to JSON along with patch version
    with open(get_file_path(CHAMPIONS_FILE), "w", encoding="utf-8") as f:
        json.dump({
            "patch": patch,
            "champions": champ_dict
        }, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved {len(champ_dict)} champions for patch {patch}")
    return champ_dict

def load_champion_list():
    champ_file_path = get_file_path(CHAMPIONS_FILE)
    if not os.path.exists(champ_file_path):
        return fetch_champion_list()

    with open(champ_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get("champions", {})

def get_stored_patch():
    champ_file_path = get_file_path(CHAMPIONS_FILE)
    if not os.path.exists(champ_file_path):
        return None
    with open(champ_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get("patch")

def update_champion_data_if_needed():
    try:
        latest_patch = fetch_latest_patch()
        stored_patch = get_stored_patch()
        if stored_patch != latest_patch:
            print(f"🔄 Updating champions.json: {stored_patch} → {latest_patch}")
            fetch_champion_list()
        else:
            print(f"✅ Champion data is up to date ({stored_patch})")
    except Exception as e:
        print(f"⚠️ Could not update champion data: {e}")

def id_to_champion_name(champ_id):
    champions = load_champion_list()
    return champions.get(str(champ_id), f"Unknown ({champ_id})")

# Optional: run directly to force update
if __name__ == "__main__":
    update_champion_data_if_needed()


"""
///////////////////////getting owned champs
///////////////////////getting owned champs
"""
import time
import psutil
import base64
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def find_league_credentials():
    """
    Finds the League Client process and extracts port and auth token from its command line.
    Returns (port, token) if found, else raises Exception.
    """
    for proc in psutil.process_iter(['name', 'cmdline']):
        if proc.info['name'] == "LeagueClientUx.exe":
            cmdline = proc.info['cmdline']
            port = None
            token = None
            time.sleep(1)
            for arg in cmdline:
                if arg.startswith("--app-port="):
                    port = arg.split("=")[1]
                elif arg.startswith("--remoting-auth-token="):
                    token = arg.split("=")[1]
            if port and token:
                return port, token
    raise Exception("League Client not found. Please make sure it's running.")

def connect_to_league():
    """
    Creates an authenticated requests.Session connected to the League Client API.
    Returns (session, base_url).
    """
    port, token = find_league_credentials()
    base_url = f"https://127.0.0.1:{port}"
    session = requests.Session()
    auth = base64.b64encode(f"riot:{token}".encode()).decode()
    session.headers.update({"Authorization": f"Basic {auth}"})
    return session, base_url

def owned_champions():
    """
    Fetches the list of owned champions and writes them to champions_owned.json.
    """
    try:
        session, base_url = connect_to_league()

        # Riot API endpoint for champions
        url = f"{base_url}/lol-champions/v1/owned-champions-minimal"
        response = session.get(url, verify=False)
        time.sleep(1)
        if response.status_code != 200:
            raise Exception(f"Error fetching champions: {response.status_code} {response.text}")

        data = response.json()

        # Create a clean list with championId and name
        owned_list = [
            {"id": champ["id"], "name": champ["name"]}
            for champ in data
            if champ.get("ownership", {}).get("owned", False)
        ]

        # Save to JSON
        with open(get_file_path("champions_owned.json"), "w", encoding="utf-8") as f:
            json.dump(owned_list, f, indent=4, ensure_ascii=False)

        print(f"✅ Saved {len(owned_list)} owned champions to champions_owned.json")

    except Exception as e:
        print(f"❌ {e}")

if __name__ == "__main__":
    owned_champions()