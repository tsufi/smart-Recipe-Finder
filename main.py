import os
import json
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from components.scrollable_frame import ScrollableFrame
from ui.search import show_search
from ui.favorites import show_favorites
from ui.history import show_history
from ui.meal_planner import MealPlannerPanel
from data.storage import load_json
from constants.paths import HISTORY_FILE, FAVORITES_FILE
from ui.recipe_tab import RecipeTab
from utils.translator import Translator
from ui.settings import show_settings
from data.settings import load_settings

class RecipeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🍽️ Recipe Finder")
        self.root.geometry("1000x720")

        settings = load_settings()
        self.language = settings.get("language", "en")
        self.translator = Translator(self.language)

        self.history = load_json(HISTORY_FILE, [])
        self.favorites = load_json(FAVORITES_FILE, [])
        self.last_ingredients = ""
        self.last_diets = []
        self.set_translated_meal_types()

        self.setup_layout()
        self.show_search()

    def set_translated_meal_types(self):
        _ = self.translator._
        self.meal_types = [
            _("any"), _("breakfast"), _("lunch"),
            _("dinner"), _("snack"), _("brunch")
        ]

    def setup_layout(self):
        self.sidebar = ttk.Frame(self.root, width=160)
        self.sidebar.pack(side="left", fill="y")

        self.main = ttk.Frame(self.root)
        self.main.pack(side="right", fill="both", expand=True)

        self.notebook = ttk.Notebook(self.main)
        self.notebook.pack(fill="both", expand=True)

        _ = self.translator._

        ttk.Button(self.sidebar, text="🔍 " + _("search"), command=self.show_search).pack(fill="x", pady=5)
        ttk.Button(self.sidebar, text="⭐ " + _("favorites"), command=self.show_favorites).pack(fill="x", pady=5)
        ttk.Button(self.sidebar, text="📜 " + _("history"), command=self.show_history).pack(fill="x", pady=5)
        ttk.Button(self.sidebar, text="🗓️ " + _("meal_planner"), command=self.show_meal_planner).pack(fill="x", pady=5)
        ttk.Button(self.sidebar, text="⚙ " + _("settings"), command=lambda: show_settings(self)).pack(pady=5)

    def clear_main(self):
        for widget in self.main.winfo_children():
            widget.destroy()
        self.notebook = ttk.Notebook(self.main)
        self.notebook.pack(fill="both", expand=True)
        
    def refresh_sidebar(self):
        # Clear old widgets
        for widget in self.sidebar.winfo_children():
            widget.destroy()

        # Prevent sidebar from collapsing
        self.sidebar.pack_propagate(False)
        self.sidebar.config(width=160)  # Same width as during setup

        # Rebuild buttons with updated translations
        _ = self.translator._

        ttk.Button(self.sidebar, text="🔍 " + _("search"), command=self.show_search).pack(fill="x", pady=5)
        ttk.Button(self.sidebar, text="⭐ " + _("favorites"), command=self.show_favorites).pack(fill="x", pady=5)
        ttk.Button(self.sidebar, text="📜 " + _("history"), command=self.show_history).pack(fill="x", pady=5)
        ttk.Button(self.sidebar, text="🗓️ " + _("meal_planner"), command=self.show_meal_planner).pack(fill="x", pady=5)
        ttk.Button(self.sidebar, text="⚙ " + _("settings"), command=lambda: show_settings(self)).pack(pady=5)

    def display_recipe_tab(self, tab_control, basic_info, full_info):
        tab = RecipeTab(self, tab_control, basic_info, full_info)
        tab_control.select(tab.tab)

    def show_search(self):
        self.clear_main()
        show_search(self)

    def show_favorites(self):
        self.clear_main()
        show_favorites(self)

    def show_history(self):
        self.clear_main()
        show_history(self)

    def show_meal_planner(self):
        self.clear_main()
        MealPlannerPanel(self.notebook, self)

    def open_recipe(self, full_info, show_close=False):
        if not self.notebook or not self.notebook.winfo_exists():
            self.notebook = ttk.Notebook(self.main)
            self.notebook.pack(fill="both", expand=True)
        tab = RecipeTab(self, self.notebook, full_info, full_info, show_close=show_close)
        self.notebook.select(tab.tab)

    def tr(self, key):
        return self.translator._(key)

    def save_config(self):
        os.makedirs("data", exist_ok=True)
        with open("data/settings.json", "w", encoding="utf-8") as f:
            json.dump({"language": self.language}, f)

    def reload_language(self):
        from utils.translator import Translator
        from ui.settings import show_settings

        # Reinitialize the translator and update meal types
        self.translator = Translator(self.language)
        self.set_translated_meal_types()

        # Clear the main area and fully reset layout
        self.clear_main()
        self.refresh_sidebar()

        # Refresh settings only once
        show_settings(self)

if __name__ == "__main__":
    root = ttk.Window(themename="darkly")
    app = RecipeApp(root)
    root.mainloop()
