import tkinter as tk
from tkinter import ttk, messagebox
import json
from champion_data import load_champion_list

CONFIG_FILE = "config.json"





import os
import sys
def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)
import os
import sys

def get_config_path():
    # For dev: relative path
    if getattr(sys, 'frozen', False):
        # Running as bundled exe
        base_path = os.path.expanduser("~/.lolmatchassistant/")
        os.makedirs(base_path, exist_ok=True)
        return os.path.join(base_path, CONFIG_FILE)
    else:
        # Running in dev mode
        return os.path.join(os.path.abspath("."), CONFIG_FILE)








class PickListUI(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.champions = load_champion_list()
        self.pick_priority = []
        self.load_config()

        self.create_widgets()
        self.refresh_pick_list_display()

    def create_widgets(self):
        header = tk.Label(self, text="Pick Priority List", font=("Arial", 14, "bold"))
        header.pack(pady=(5, 10))

        self.pick_list_frame = tk.Frame(self)
        self.pick_list_frame.pack(fill=tk.X)

        ttk.Separator(self, orient="horizontal").pack(fill=tk.X, pady=5)

        self.add_frame = tk.Frame(self)
        self.add_frame.pack(fill=tk.X, pady=5)

        tk.Label(self.add_frame, text="Add Champion:").pack(side=tk.LEFT)

        sorted_champs = sorted(self.champions.items(), key=lambda kv: kv[1])
        self.champ_dropdown_values = [f"{name} ({champ_id})" for champ_id, name in sorted_champs]
        self.champ_id_map = {f"{name} ({champ_id})": champ_id for champ_id, name in sorted_champs}

        self.champ_var = tk.StringVar()
        self.champ_dropdown = ttk.Combobox(self.add_frame, values=self.champ_dropdown_values, textvariable=self.champ_var, state="readonly")
        self.champ_dropdown.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5))

        self.add_button = tk.Button(self.add_frame, text="Add", command=self.add_champion)
        self.add_button.pack(side=tk.LEFT)

    def refresh_pick_list_display(self):
        for widget in self.pick_list_frame.winfo_children():
            widget.destroy()

        if not self.pick_priority:
            tk.Label(self.pick_list_frame, text="No champions in pick list").pack()
            return

        for i, champ_id in enumerate(self.pick_priority, start=1):
            name = self.champions.get(champ_id, f"Unknown ({champ_id})")
            frame = tk.Frame(self.pick_list_frame)
            frame.pack(fill=tk.X, pady=1)

            lbl = tk.Label(frame, text=f"{i}. {name} ({champ_id})", anchor="w")
            lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)

            btn = tk.Button(frame, text="X", command=lambda cid=champ_id: self.remove_champion(cid), fg="red", width=2)
            btn.pack(side=tk.RIGHT)

    def add_champion(self):
        selected = self.champ_var.get()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a champion to add.")
            return

        champ_id = self.champ_id_map[selected]
        if champ_id in self.pick_priority:
            messagebox.showinfo("Already Added", f"{self.champions[champ_id]} is already in the pick list.")
            return

        if len(self.pick_priority) >= 10:
            messagebox.showwarning("Limit Reached", "Maximum 10 champions can be picked.")
            return

        self.pick_priority.append(champ_id)
        self.save_config()
        self.refresh_pick_list_display()

    def remove_champion(self, champ_id):
        if champ_id in self.pick_priority:
            self.pick_priority.remove(champ_id)
            self.save_config()
            self.refresh_pick_list_display()

    def load_config(self):
        try:
            with open(resource_path(CONFIG_FILE), "r", encoding="utf-8") as f:

                data = json.load(f)
                self.pick_priority = data.get("pick_priority", [])
        except Exception:
            self.pick_priority = []

    def save_config(self):
        try:
            with open(resource_path(CONFIG_FILE), "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}

        data["pick_priority"] = self.pick_priority  # or "pick_priority" in pick_list_ui.py
        # CHANGE THIS:
        with open(resource_path(CONFIG_FILE), "w", encoding="utf-8") as f:  # <-- must be "w" not "r"
            json.dump(data, f, indent=4)
