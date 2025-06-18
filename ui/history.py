#ui/history.py
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from components.scrollable_frame import ScrollableFrame
from services.storage import get_history
from services.search import show_search

def show_history(app):
    app.clear_main()

    history = get_history()

    if isinstance(history, str):
        history = [history]
    elif not isinstance(history, list):
        history = []

    sf = ScrollableFrame(app.main)
    sf.pack(fill="both", expand=True, padx=10, pady=10)

    ttk.Label(sf.scrollable_frame, text=app.tr("search_history"), font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=5)

    if not history:
        ttk.Label(sf.scrollable_frame, text=app.tr("no_searches"), font=("Segoe UI", 11)).pack(anchor="w", pady=5)
        return

    for item in history:
        if isinstance(item, list):
            item = "".join(item)
        elif not isinstance(item, str):
            continue

        ttk.Button(
            sf.scrollable_frame,
            text=f"🔍 {item}",
            bootstyle="secondary-link",
            command=lambda i=item: show_search(app, prefill=i)
        ).pack(anchor="w", pady=2)
