#ui/favorites.py
import tkinter as tk
import tkinter.messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from services.recipes import get_recipe_info


class FavoritesPanel:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.setup_ui()

    def setup_ui(self):
        frame = ttk.Frame(self.parent)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        if not self.app.favorites:
            ttk.Label(frame, text=self.app.tr("no_favorites"), font=("Segoe UI", 16)).pack(pady=20)
            return

        for fav in self.app.favorites:
            self.create_favorite_entry(frame, fav)

    def create_favorite_entry(self, frame, fav):
        fav_frame = ttk.Frame(frame)
        fav_frame.pack(fill="x", pady=5)

        ttk.Label(fav_frame, text=fav['title'], font=("Segoe UI", 12, "bold")).pack(side="left", anchor="w", padx=10)

        ttk.Button(fav_frame, text=self.app.tr("view"), command=lambda: self.view_favorite_recipe(fav)).pack(side="right", padx=5)

        ttk.Button(fav_frame, text=self.app.tr("remove"), bootstyle="danger", command=lambda: self.remove_favorite(fav)).pack(side="right")

    def view_favorite_recipe(self, fav):
        recipe = get_recipe_info(fav['id'])

        if not recipe:
            tk.messagebox.showwarning(self.app.tr("not_found"), "This recipe is no longer available.")
            return

        self.app.clear_main()
        recipe_notebook = ttk.Notebook(self.app.main)
        recipe_notebook.pack(fill="both", expand=True, padx=10, pady=10)
        self.app.display_recipe_tab(recipe_notebook, fav, recipe)

    def remove_favorite(self, fav):
        self.app.favorites = [f for f in self.app.favorites if f["id"] != fav["id"]]
        from services.storage import save_favorites
        save_favorites(self.app.favorites)
        self.app.show_favorites()


def show_favorites(app):
    app.clear_main()
    FavoritesPanel(app.main, app)
