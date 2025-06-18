#ui/layout.py
import ttkbootstrap as ttk
from services.search import show_search
from ui.favorites import show_favorites
from ui.history import show_history
from ui.meal_planner import show_meal_planner

def setup_layout(app):
    sidebar = ttk.Frame(app.root, width=150)
    sidebar.pack(side="left", fill="y")

    main = ttk.Frame(app.root)
    main.pack(side="right", fill="both", expand=True)

    ttk.Button(sidebar, text="🔍 Search", bootstyle="primary", command=lambda: app.show_search()).pack(fill="x", pady=5)
    ttk.Button(sidebar, text="⭐ Favorites", bootstyle="primary", command=lambda: app.show_favorites()).pack(fill="x", pady=5)
    ttk.Button(sidebar, text="📜 History", bootstyle="primary", command=lambda: app.show_history()).pack(fill="x", pady=5)
    ttk.Button(sidebar, text="🗓️ Meal Planner", bootstyle="primary", command=lambda: app.show_meal_planner()).pack(fill="x", pady=5)

    def clear_main():
        for widget in main.winfo_children():
            widget.destroy()

    app.clear_main = clear_main
    app.show_search = lambda: show_search(app)
    app.show_favorites = lambda: show_favorites(app)
    app.show_history = lambda: show_history(app)
    app.show_meal_planner = lambda: show_meal_planner(app)

    return sidebar, main
