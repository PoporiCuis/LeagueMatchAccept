import requests
import json
import os


CHAMPIONS_FILE = "champions.json"




import os
import sys


def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)






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
    with open(resource_path(CHAMPIONS_FILE), "w", encoding="utf-8") as f:
        json.dump({
            "patch": patch,
            "champions": champ_dict
        }, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved {len(champ_dict)} champions for patch {patch}")
    return champ_dict

def load_champion_list():
    if not os.path.exists(resource_path(CHAMPIONS_FILE)): 
        return fetch_champion_list()
    
    with open(resource_path(CHAMPIONS_FILE), "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get("champions", {})

def get_stored_patch():
    if not os.path.exists(resource_path(CHAMPIONS_FILE)): 
        return None
    with open(resource_path(CHAMPIONS_FILE), "r", encoding="utf-8") as f:
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
