import base64
import psutil
import re
import requests


def find_league_credentials():
    # Search for the League client process and extract its port and auth token.
    for proc in psutil.process_iter(['cmdline']):
        try:
            cmdline_list = proc.info.get('cmdline')
            if not cmdline_list:
                continue
            cmdline = ' '.join(cmdline_list)

            if 'LeagueClientUx.exe' in cmdline:
                port_match = re.search(r'--app-port=(\d+)', cmdline)
                token_match = re.search(r'--remoting-auth-token=([\w-]+)', cmdline)

                if port_match and token_match:
                    port = port_match.group(1)
                    token = token_match.group(1)
                    auth = base64.b64encode(f"riot:{token}".encode()).decode()
                    return {"port": port, "auth": auth}
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            continue
    return None


def connect_to_league():
    """Return an authenticated session only when the League API responds."""
    credentials = find_league_credentials()
    if not credentials:
        return None, None

    base_url = f"https://127.0.0.1:{credentials['port']}"
    session = requests.Session()
    session.headers.update({"Authorization": f"Basic {credentials['auth']}"})

    try:
        response = session.get(
            f"{base_url}/lol-gameflow/v1/gameflow-phase",
            verify=False,
            timeout=3,
        )
        if response.status_code != 200:
            session.close()
            return None, None
    except requests.RequestException:
        session.close()
        return None, None

    return session, base_url


def get_ready_check_state(session, base_url):
    try:
        response = session.get(f"{base_url}/lol-matchmaking/v1/ready-check", verify=False)
        if response.status_code == 200:
            ready_check = response.json()
            return ready_check.get('state'), 200
        return None, response.status_code
    except Exception:
        return None, None


def accept_ready_check(session, base_url):
    # Attempt to accept the ready check. Returns True if accepted (204).
    try:
        response = session.post(f"{base_url}/lol-matchmaking/v1/ready-check/accept", verify=False)
        return response.status_code == 204
    except Exception:
        return False


def get_champ_select_status(session, base_url):
    # Return the HTTP status code for the champion select session endpoint.
    try:
        response = session.get(f"{base_url}/lol-champ-select/v1/session", verify=False)
        return response.status_code
    except Exception:
        return None
