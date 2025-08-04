# client_state.py

import requests

import os
import sys


def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)





# Gameflow phase constants
STATE_NONE = "NONE"
STATE_LOBBY = "LOBBY"
STATE_MATCHMAKING = "MATCHMAKING"
STATE_READY_CHECK = "READYCHECK"
STATE_CHAMP_SELECT = "CHAMPSELECT"
STATE_GAME_START = "GAMESTART"
STATE_IN_GAME = "INGAME"
STATE_WAITING_FOR_STATS = "WAITINGFORSTATS"
STATE_END_OF_GAME = "ENDOFGAME"

# All known gameflow states for reference
ALL_STATES = {
    STATE_NONE,
    STATE_LOBBY,
    STATE_MATCHMAKING,
    STATE_READY_CHECK,
    STATE_CHAMP_SELECT,
    STATE_GAME_START,
    STATE_IN_GAME,
    STATE_WAITING_FOR_STATS,
    STATE_END_OF_GAME
}

def get_client_state(session: requests.Session, base_url: str) -> str:
    # Fetch the current client state from the League API
    try:
        response = session.get(f"{base_url}/lol-gameflow/v1/gameflow-phase", timeout=5)
        response.raise_for_status()
        # Use response.text and strip quotes instead of response.json()
        state = response.text.strip('"').upper()
        return state if state in ALL_STATES else STATE_NONE
    except Exception:
        return STATE_NONE


# State check helpers
def is_in_lobby(state: str) -> bool:
    return state == STATE_LOBBY

def is_in_matchmaking(state: str) -> bool:
    return state == STATE_MATCHMAKING

def is_in_ready_check(state: str) -> bool:
    return state == STATE_READY_CHECK

def is_in_champ_select(state: str) -> bool:
    return state == STATE_CHAMP_SELECT

def is_in_game(state: str) -> bool:
    return state == STATE_IN_GAME

def is_idle(state: str) -> bool:
    # Returns True if the client is idle (not in matchmaking, champ select, or in-game)
    return state in {STATE_NONE, STATE_LOBBY, STATE_END_OF_GAME, STATE_WAITING_FOR_STATS}
