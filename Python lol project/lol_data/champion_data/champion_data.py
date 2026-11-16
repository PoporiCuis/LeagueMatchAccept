import json
import os
import requests

from exe_stuff import get_file_path
from league_api.api_client import connect_to_league

CHAMPIONS_FILE = "champions.json"


def fetch_latest_patch():
    url = "https://ddragon.leagueoflegends.com/api/versions.json"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()[0]


def fetch_champion_list(patch=None):
    if patch is None:
        patch = fetch_latest_patch()

    url = f"https://ddragon.leagueoflegends.com/cdn/{patch}/data/en_US/champion.json"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()["data"]

    champions = {
        int(champion["key"]): champion["name"]
        for champion in data.values()
    }

    with open(get_file_path(CHAMPIONS_FILE), "w", encoding="utf-8") as champion_file:
        json.dump(
            {"patch": patch, "champions": champions},
            champion_file,
            indent=2,
            ensure_ascii=False,
        )

    print(f"✅ Saved {len(champions)} champions for patch {patch}")
    return champions


def load_champion_list():
    champion_path = get_file_path(CHAMPIONS_FILE)
    if not os.path.exists(champion_path):
        return fetch_champion_list()

    with open(champion_path, "r", encoding="utf-8") as champion_file:
        data = json.load(champion_file)
        return data.get("champions", {})


def get_stored_patch():
    champion_path = get_file_path(CHAMPIONS_FILE)
    if not os.path.exists(champion_path):
        return None

    with open(champion_path, "r", encoding="utf-8") as champion_file:
        data = json.load(champion_file)
        return data.get("patch")


def update_champion_data_if_needed():
    try:
        latest_patch = fetch_latest_patch()
        stored_patch = get_stored_patch()
        if stored_patch != latest_patch:
            print(f"🔄 Updating champions.json: {stored_patch} → {latest_patch}")
            fetch_champion_list(latest_patch)
        else:
            print(f"✅ Champion data is up to date ({stored_patch})")
    except Exception as error:
        print(f"⚠️ Could not update champion data: {error}")


def id_to_champion_name(champ_id):
    champions = load_champion_list()
    return champions.get(str(champ_id), f"Unknown ({champ_id})")


def owned_champions(session=None, base_url=None):
    """Save the connected account's owned champions to the local data file."""
    owns_session = session is None or base_url is None
    if owns_session:
        session, base_url = connect_to_league()
        if session is None:
            print("❌ League Client not found.")
            return

    try:
        url = f"{base_url}/lol-champions/v1/owned-champions-minimal"
        response = session.get(url, verify=False, timeout=5)
        response.raise_for_status()

        owned_list = [
            {"id": champion["id"], "name": champion["name"]}
            for champion in response.json()
            if champion.get("ownership", {}).get("owned", False)
        ]

        with open(get_file_path("champions_owned.json"), "w", encoding="utf-8") as owned_file:
            json.dump(owned_list, owned_file, indent=4, ensure_ascii=False)

        print(f"✅ Saved {len(owned_list)} owned champions to champions_owned.json")
    except Exception as error:
        print(f"❌ Could not load owned champions: {error}")
    finally:
        if owns_session and session is not None:
            session.close()


if __name__ == "__main__":
    update_champion_data_if_needed()
    owned_champions()
