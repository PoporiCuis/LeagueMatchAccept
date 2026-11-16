import json
import threading
import tkinter as tk

from PIL import Image

from exe_stuff import get_config_path, resource_path
from gui import tray
from gui.ban_list_ui import BanListUI
from gui.pick_list_ui import PickListUI
from league_api.api_client import connect_to_league
from main_loop import start_monitor_loop

CONFIG_FILE = "config.json"


def create_tray_image():
    return Image.open(resource_path("minion.ico"))


def start_gui(
    session,
    base_url,
    client_connected,
    on_connected=None,
    summoner_id=None,
):
    root = tk.Tk()
    root.title("LoL Match Assistant")
    root.geometry("600x450")

    with open(get_config_path(CONFIG_FILE), "r", encoding="utf-8") as config_file:
        config = json.load(config_file)

    status_var = tk.StringVar()
    status_label = tk.Label(root, textvariable=status_var, font=("Arial", 12))
    status_label.pack(pady=8)

    connection_frame = tk.Frame(root)
    connection_message = tk.Label(
        connection_frame,
        text="",
        font=("Arial", 12),
        wraplength=520,
        justify=tk.CENTER,
    )
    connection_message.pack(pady=(35, 12))

    countdown_var = tk.StringVar()
    countdown_label = tk.Label(connection_frame, textvariable=countdown_var)
    countdown_label.pack(pady=6)

    main_frame = tk.Frame(root)
    connection_state = {
        "mode": "startup",
        "checking": False,
        "countdown": 30,
        "timer": None,
    }
    monitor_state = {"stop_event": None, "thread": None}
    client_state = {"session": None, "base_url": None}

    def cancel_countdown():
        timer = connection_state["timer"]
        if timer is not None:
            try:
                root.after_cancel(timer)
            except tk.TclError:
                pass
            connection_state["timer"] = None

    def schedule_countdown():
        if connection_state["mode"] != "startup" or connection_state["checking"]:
            return
        remaining = connection_state["countdown"]
        countdown_var.set(f"Retrying automatically in {remaining} seconds…")
        if remaining <= 0:
            connection_state["timer"] = None
            attempt_connection()
            return
        connection_state["countdown"] -= 1
        connection_state["timer"] = root.after(1000, schedule_countdown)

    def show_startup_connection_screen():
        connection_state["mode"] = "startup"
        connection_state["countdown"] = 30
        connection_message.config(
            text="League Client not found. Open the client and this app will keep checking."
        )
        retry_button.config(text="Retry now", state=tk.NORMAL)
        if not connection_frame.winfo_manager():
            connection_frame.pack(fill=tk.BOTH, expand=True)
        schedule_countdown()

    def show_disconnected_screen():
        cancel_countdown()
        stop_event = monitor_state["stop_event"]
        if stop_event is not None:
            stop_event.set()

        old_session = client_state["session"]
        if old_session is not None:
            try:
                old_session.close()
            except Exception:
                pass

        client_state["session"] = None
        client_state["base_url"] = None
        connection_state["mode"] = "disconnected"
        connection_state["checking"] = False
        connection_message.config(text="Client closed. Click below to retry the connection.")
        countdown_var.set("")
        retry_button.config(text="Retry connection", state=tk.NORMAL)
        main_frame.pack_forget()
        if not connection_frame.winfo_manager():
            connection_frame.pack(fill=tk.BOTH, expand=True)
        status_var.set("League Client connection lost.")

    def handle_disconnect():
        try:
            root.after(0, show_disconnected_screen)
        except tk.TclError:
            pass

    def update_status(text):
        try:
            root.after(0, lambda: status_var.set(text) if root.winfo_exists() else None)
        except tk.TclError:
            pass

    def build_connected_screen(new_session, new_base_url, current_summoner_id):
        cancel_countdown()
        connection_state["checking"] = False
        connection_state["mode"] = "connected"
        client_state["session"] = new_session
        client_state["base_url"] = new_base_url
        retry_button.config(state=tk.NORMAL)
        connection_frame.pack_forget()

        for widget in main_frame.winfo_children():
            widget.destroy()

        try:
            with open(get_config_path(CONFIG_FILE), "r", encoding="utf-8") as config_file:
                current_config = json.load(config_file)
        except (OSError, json.JSONDecodeError):
            current_config = config

        toggles_frame = tk.Frame(main_frame)
        toggles_frame.pack(fill=tk.X, padx=10, pady=5)

        auto_accept_var = tk.BooleanVar(value=current_config.get("auto_accept", False))
        auto_ban_var = tk.BooleanVar(value=current_config.get("auto_ban", False))
        auto_pick_var = tk.BooleanVar(value=current_config.get("auto_pick", False))
        role_detect_var = tk.BooleanVar(value=current_config.get("auto_detect_role", False))

        def save_toggle_config():
            try:
                with open(get_config_path(CONFIG_FILE), "r", encoding="utf-8") as config_file:
                    data = json.load(config_file)
            except (OSError, json.JSONDecodeError):
                data = {}

            data["auto_accept"] = auto_accept_var.get()
            data["auto_ban"] = auto_ban_var.get()
            data["auto_pick"] = auto_pick_var.get()
            data["auto_detect_role"] = role_detect_var.get()

            with open(get_config_path(CONFIG_FILE), "w", encoding="utf-8") as config_file:
                json.dump(data, config_file, indent=4)

        tk.Checkbutton(
            toggles_frame,
            text="Enable Auto Accept",
            variable=auto_accept_var,
            command=save_toggle_config,
        ).pack(side=tk.LEFT, padx=10)
        tk.Checkbutton(
            toggles_frame,
            text="Enable Auto Ban",
            variable=auto_ban_var,
            command=save_toggle_config,
        ).pack(side=tk.LEFT, padx=10)
        tk.Checkbutton(
            toggles_frame,
            text="Enable Auto Pick",
            variable=auto_pick_var,
            command=save_toggle_config,
        ).pack(side=tk.LEFT, padx=10)
        tk.Checkbutton(
            toggles_frame,
            text="Enable Role Detection",
            variable=role_detect_var,
            command=save_toggle_config,
        ).pack(side=tk.LEFT, padx=10)

        lists_frame = tk.Frame(main_frame)
        lists_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ban_ui = BanListUI(lists_frame)
        ban_ui.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        pick_ui = PickListUI(lists_frame)
        pick_ui.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        main_frame.pack(fill=tk.BOTH, expand=True)
        status_var.set("Connected to League Client.")

        stop_event = threading.Event()
        monitor_state["stop_event"] = stop_event
        monitor_state["thread"] = start_monitor_loop(
            new_session,
            new_base_url,
            stop_event,
            update_status,
            pick_ui,
            ban_ui,
            current_summoner_id or current_config.get("SummonerID"),
            on_disconnect=handle_disconnect,
        )

    def connection_failed():
        connection_state["checking"] = False
        retry_button.config(state=tk.NORMAL)
        if connection_state["mode"] == "startup":
            connection_message.config(
                text="League Client not ready yet. Open it and the app will keep checking."
            )
            connection_state["countdown"] = 30
            schedule_countdown()
        else:
            connection_message.config(text="Client unavailable. Click below to try again.")
            countdown_var.set("")

    def attempt_connection():
        if connection_state["checking"]:
            return
        cancel_countdown()
        connection_state["checking"] = True
        retry_button.config(state=tk.DISABLED)
        countdown_var.set("Checking for League Client…")
        connection_message.config(text="Looking for the League Client…")

        def check_in_background():
            new_session, new_base_url = connect_to_league()
            if new_session is None:
                try:
                    root.after(0, connection_failed)
                except tk.TclError:
                    pass
                return

            try:
                new_summoner_id = on_connected(new_session, new_base_url) if on_connected else None
            except Exception:
                new_session.close()
                try:
                    root.after(0, connection_failed)
                except tk.TclError:
                    pass
                return

            try:
                root.after(
                    0,
                    lambda: build_connected_screen(
                        new_session,
                        new_base_url,
                        new_summoner_id,
                    ),
                )
            except tk.TclError:
                new_session.close()

        threading.Thread(target=check_in_background, daemon=True).start()

    retry_button = tk.Button(connection_frame, text="Retry now", command=attempt_connection)
    retry_button.pack(pady=12)

    def quit_app(icon):
        stop_event = monitor_state["stop_event"]
        if stop_event is not None:
            stop_event.set()
        icon.stop()
        try:
            root.after(0, root.destroy)
        except tk.TclError:
            pass

    icon = tray.start_tray(root, create_tray_image(), quit_app)

    def on_close():
        root.withdraw()

    root.protocol("WM_DELETE_WINDOW", on_close)

    if client_connected and session is not None and base_url is not None:
        build_connected_screen(session, base_url, summoner_id or config.get("SummonerID"))
    else:
        show_startup_connection_screen()

    root.mainloop()
