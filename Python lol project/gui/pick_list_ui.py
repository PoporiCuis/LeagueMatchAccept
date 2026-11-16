import tkinter as tk
import os
import sys
import json

from tkinter import ttk, messagebox

CONFIG_FILE = "config.json"

#exe stuff???
from exe_stuff import get_file_path, get_config_path, resource_path
# Remove problematic file load at import time
#end of exe stuff

def load_owned_champions():
    try:
        with open(get_file_path("champions_owned.json"), "r", encoding="utf-8") as f:
            data = json.load(f)
        # Convert from list of dicts to {id: name}
        return {champ["id"]: champ["name"] for champ in data}
    except Exception as e:
        print(f"❌ Could not load champions_owned.json: {e}")
        return {}

class PickListUI(tk.Frame):
    PROFILE_NAMES = ["Top", "Jungle", "Mid", "ADC", "Support", "Custom"]

    def __init__(self, parent):
        super().__init__(parent)
        self.champions = load_owned_champions()
        self.pick_priority_profiles = {}  # dict of profile_name -> list of champ_ids
        self.current_profile = None  # will be set by config


        self.load_config()
        self.create_widgets()

        if self.current_profile:
            self.profile_var.set(self.current_profile)
        self.refresh_pick_list_display()

    def create_widgets(self):
        header = tk.Label(self, text="Pick Priority List", font=("Arial", 14, "bold"))
        header.pack(pady=(5, 10))

        # Profile selector dropdown
        profile_frame = tk.Frame(self)
        profile_frame.pack(fill=tk.X, pady=(0, 10))
        tk.Label(profile_frame, text="Select Profile:").pack(side=tk.LEFT)

        self.profile_var = tk.StringVar(value=self.current_profile)
        self.profile_dropdown = ttk.Combobox(
            profile_frame,
            values=self.PROFILE_NAMES,
            textvariable=self.profile_var,
            state="readonly",
            width=10
        )
        self.profile_dropdown.pack(side=tk.LEFT, padx=5)
        self.profile_dropdown.bind("<<ComboboxSelected>>", self.on_profile_change)

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
        self.champ_dropdown = ttk.Combobox(
            self.add_frame,
            values=self.champ_dropdown_values,
            textvariable=self.champ_var,
            state="readonly"
        )
        self.champ_dropdown.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5))
        self.champ_dropdown.bind("<KeyPress>", self.on_keypress_jump)

        self.add_button = tk.Button(self.add_frame, text="Add", command=self.add_champion)
        self.add_button.pack(side=tk.LEFT)

        # Profile display section
        ttk.Separator(self, orient="horizontal").pack(fill=tk.X, pady=5)

        profiles_header = tk.Label(self, text="Saved Profiles:", font=("Arial", 10, "bold"))
        profiles_header.pack(anchor="w", padx=5)

        self.profiles_display_frame = tk.Frame(self)
        self.profiles_display_frame.pack(fill=tk.X, padx=5, pady=5)

        self.refresh_profiles_display()

    def refresh_pick_list_display(self):
        for widget in self.pick_list_frame.winfo_children():
            widget.destroy()

        current_list = self.pick_priority_profiles.get(self.current_profile, [])
        if not current_list:
            tk.Label(self.pick_list_frame, text="No champions in pick list").pack()
            return

        for i, champ_id in enumerate(current_list, start=1):
            name = self.champions.get(champ_id, f"Unknown ({champ_id})")
            frame = tk.Frame(self.pick_list_frame)
            frame.pack(fill=tk.X, pady=1)

            lbl = tk.Label(frame, text=f"{i}. {name} ({champ_id})", anchor="w")
            lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)

            btn = tk.Button(
                frame,
                text="X",
                command=lambda cid=champ_id: self.remove_champion(cid),
                fg="red",
                width=2
            )
            btn.pack(side=tk.RIGHT)

        self.refresh_profiles_display()

    def refresh_profiles_display(self):
        """Display all saved profiles with their champions"""
        for widget in self.profiles_display_frame.winfo_children():
            widget.destroy()

        for profile_name in self.PROFILE_NAMES:
            champ_list = self.pick_priority_profiles.get(profile_name, [])
            if not champ_list:  # Skip empty profiles
                continue

            profile_frame = tk.Frame(self.profiles_display_frame)
            profile_frame.pack(fill=tk.X, pady=2)

            # Create champion names list
            champ_names = [self.champions.get(cid, f"Unknown({cid})") for cid in champ_list[:3]]  # Show first 3
            champ_text = ", ".join(champ_names)
            if len(champ_list) > 3:
                champ_text += f" (+{len(champ_list)-3} more)"

            # Profile label (clickable)
            profile_label = tk.Label(
                profile_frame,
                text=f"{profile_name}: {champ_text}",
                cursor="hand2",
                fg="blue",
                anchor="w"
            )
            profile_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
            profile_label.bind("<Button-1>", lambda e, p=profile_name: self.load_profile(p))

            # X button to clear profile
            clear_btn = tk.Button(
                profile_frame,
                text="X",
                command=lambda p=profile_name: self.clear_profile(p),
                fg="red",
                width=2,
                font=("Arial", 8)
            )
            clear_btn.pack(side=tk.RIGHT)

    def load_profile(self, profile_name):
        """Load a profile into current selection"""
        self.profile_var.set(profile_name)
        self.current_profile = profile_name
        self.refresh_pick_list_display()
        self.save_config()

    def clear_profile(self, profile_name):
        """Clear all champions from a profile"""
        if messagebox.askyesno("Clear Profile", f"Clear all champions from {profile_name} profile?"):
            self.pick_priority_profiles[profile_name] = []
            self.save_config()
            self.refresh_profiles_display()
            if self.current_profile == profile_name:
                self.refresh_pick_list_display()

    def update_pick_role_ui(self, new_profile):
        if new_profile == self.current_profile:
            return  # No need to update
        if hasattr(self, "profile_var"):
            self.profile_var.set(new_profile)
            self.current_profile = new_profile
            self.refresh_pick_list_display()

    def add_champion(self):
        selected = self.champ_var.get()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a champion to add.")
            return

        champ_id = self.champ_id_map[selected]
        current_list = self.pick_priority_profiles.setdefault(self.current_profile, [])

        if champ_id in current_list:
            messagebox.showinfo("Already Added", f"{self.champions[champ_id]} is already in the pick list.")
            return

        if len(current_list) >= 10:
            messagebox.showwarning("Limit Reached", "Maximum 10 champions can be picked.")
            return

        current_list.append(champ_id)
        self.save_config()
        self.refresh_pick_list_display()
        self.champ_var.set("")  # Clear selection

    def remove_champion(self, champ_id):
        current_list = self.pick_priority_profiles.get(self.current_profile, [])
        if champ_id in current_list:
            current_list.remove(champ_id)
            self.save_config()
            self.refresh_pick_list_display()

    def on_profile_change(self, event=None):
        self.current_profile = self.profile_var.get()
        self.save_config()
        self.refresh_pick_list_display()

    def load_config(self):
        try:
            with open(get_config_path(CONFIG_FILE), "r", encoding="utf-8") as f:
                data = json.load(f)
                self.pick_priority_profiles = data.get("pick_priority_profiles", {})
                self.current_profile = data.get("last_pick_profile", None)
        except Exception:
            self.pick_priority_profiles = {}

        # Ensure all profiles exist
        for profile in self.PROFILE_NAMES:
            if profile not in self.pick_priority_profiles:
                self.pick_priority_profiles[profile] = []

        if not self.current_profile or self.current_profile not in self.PROFILE_NAMES:
            self.current_profile = None

    def save_config(self):
        try:
            with open(get_config_path(CONFIG_FILE), "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}

        data["pick_priority_profiles"] = self.pick_priority_profiles
        data["last_pick_profile"] = self.current_profile

        with open(get_config_path(CONFIG_FILE), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def on_keypress_jump(self, event):
        if self.champ_dropdown.focus_get() != self.champ_dropdown:
            return

        letter = event.char.lower()
        if not letter.isalpha():
            return

        for i, item in enumerate(self.champ_dropdown_values):
            name = item.split(' (')[0]
            if name.lower().startswith(letter):
                self.champ_dropdown.current(i)
                break