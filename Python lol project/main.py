import os
import sys
import json
import requests
import urllib3
from league_api import find_league_credentials
from gui.interface import start_gui

import os
import sys

def get_config_path(filename="config.json"):
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle
        base_path = os.path.dirname(sys.executable)  # Folder of the EXE
    else:
        # Running as normal script
        base_path = os.path.abspath(".")

    return os.path.join(base_path, filename)

def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)

import json

def load_config():
    path = get_config_path()
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
    
def save_config(data):
    path = get_config_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


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

if __name__ == "__main__":
    urllib3.disable_warnings()
    config = load_config()
    session, base_url = connect_to_league()

    if session is None:
        print("❌ League Client not found. Launching UI with warning.")
        start_gui(None, None, client_connected=False)
    else:
        print("✅ Connected to League Client.")
        start_gui(session, base_url, client_connected=True)
