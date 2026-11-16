#auto_role.py
# This module contains the function to detect the role of a player in a game session
def detect_role(session_json, my_summoner_id, ranked_role_map, fallback_role):
    detected_role = fallback_role
    print(f"DEBUG: detected role: {detected_role} = fallback_role: {fallback_role}")
    try:
        for player in session_json.get("myTeam", []):
            if player.get("gameName") == my_summoner_id:
                detected_role = player.get("assignedPosition")
                print(f"DEBUG: We got position so now detected role: {detected_role} = fallback_role: {fallback_role}")
                break

        if detected_role in ranked_role_map:
            detected_role = ranked_role_map[detected_role]
            print(f"DEBUG: Again, we detected the role so we checked names so now detected role: {detected_role} = fallback_role: {fallback_role}")
        else:
            print(f"DEBUG: we falled back and detected role: {detected_role} = fallback_role: {fallback_role}")
            detected_role = fallback_role

    except Exception as e:
        print(f"Role detection error: {e}")
    return detected_role