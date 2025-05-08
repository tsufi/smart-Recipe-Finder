#ui/settings.py
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import json
import os

SETTINGS_PATH = "data/settings.json"
LANGUAGES = {
    "en": "English",
    "fi": "Finnish",
    "de": "German",
    "es": "Spanish",
    "fr": "French"
}

class SettingsPanel:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.current_language = app.language  # load from app, not from file
        self.setup_ui()

    def setup_ui(self):
        for widget in self.parent.winfo_children():
            widget.destroy()

        ttk.Label(self.parent, text="⚙ " + self.app.tr("settings"), font=("Segoe UI", 18, "bold")).pack(pady=20)

        frame = ttk.Frame(self.parent)
        frame.pack(pady=10)

        ttk.Label(frame, text=self.app.tr("Language") + ":", font=("Segoe UI", 12)).grid(row=0, column=0, sticky="w", padx=10, pady=5)

        self.lang_var = tk.StringVar(value=self.current_language)
        dropdown = ttk.Combobox(frame, textvariable=self.lang_var, values=list(LANGUAGES.keys()), state="readonly")
        dropdown.grid(row=0, column=1, padx=10, pady=5)

        ttk.Button(self.parent, text="💾 " + self.app.tr("save"), bootstyle="success", command=self.save).pack(pady=15)

    def save(self):
        lang = self.lang_var.get()
        self.app.language = lang
        self.app.save_config()
        tk.messagebox.showinfo(self.app.tr("settings_saved"), f"Language set to: {lang}")
        self.app.reload_language()


def show_settings(app):
    app.clear_main()
    SettingsPanel(app.main, app)
