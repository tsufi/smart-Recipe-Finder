import tkinter as tk
import tkinter.messagebox
import random
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from constants.diets import ALL_DIETS as DIETS
from api.recipes import find_by_ingredients, get_recipe_info, matches_diet
from data.storage import save_history

def show_search(app):
    app.clear_main()

    panel = ttk.Frame(app.main)
    panel.pack(fill="both", expand=True, padx=10, pady=10)

    ing_frame = ttk.Labelframe(panel, text=app.tr("ingredients"))
    ing_frame.pack(fill="x", pady=5)
    ing_entry = ttk.Entry(ing_frame)
    ing_entry.pack(fill="x", padx=5, pady=5)
    ing_entry.insert(0, app.last_ingredients)
    ttk.Label(ing_frame, text=app.tr("ingredient_hint"), foreground="gray").pack(padx=5, anchor="w")


    filters = ttk.Labelframe(panel, text=app.tr("filters"))
    filters.pack(fill="x", pady=5)

    diet_frame = ttk.Frame(filters)
    diet_frame.pack(fill="x", pady=5)
    diet_vars = {diet: tk.BooleanVar(value=diet in app.last_diets) for diet in DIETS}
    for i, (diet, var) in enumerate(diet_vars.items()):
        ttk.Checkbutton(
            diet_frame,
            text=diet.title(),
            variable=var,
            bootstyle="info"
        ).grid(row=i // 3, column=i % 3, sticky="w", padx=5, pady=2)

    time_frame = ttk.Frame(filters)
    time_frame.pack(fill="x", pady=5)
    time_min = tk.IntVar(value=0)
    time_max = tk.IntVar(value=60)

    ttk.Label(time_frame, text=app.tr("min_time")).grid(row=0, column=0, sticky="w")
    min_label = ttk.Label(time_frame, text=app.tr("0_min"))
    min_label.grid(row=0, column=1, sticky="w")
    ttk.Scale(time_frame, from_=0, to=120, orient="horizontal",
              command=lambda v: update_time_label(time_min, min_label, v)).grid(row=1, column=0, columnspan=2, sticky="ew", padx=5)

    ttk.Label(time_frame, text=app.tr("max_time")).grid(row=2, column=0, sticky="w")
    max_label = ttk.Label(time_frame, text=app.tr("60_min"))
    max_label.grid(row=2, column=1, sticky="w")
    ttk.Scale(time_frame, from_=0, to=120, orient="horizontal",
              command=lambda v: update_time_label(time_max, max_label, v)).grid(row=3, column=0, columnspan=2, sticky="ew", padx=5)

    ttk.Label(filters, text=app.tr("meal_type")).pack(anchor="w")
    meal_type_filter = ttk.Combobox(filters, values=app.meal_types, state="readonly")
    meal_type_filter.set(app.tr("any"))
    meal_type_filter.pack(fill="x", padx=5, pady=(0, 5))

    ttk.Button(panel, text=app.tr("find_recipes"), bootstyle="success", command=lambda: run_search()).pack(pady=10)

    tab_control = ttk.Notebook(app.main)
    tab_control.pack(fill="both", expand=True, padx=10, pady=10)

    def run_search():
        ingredients = [x.strip() for x in ing_entry.get().split(",") if x.strip()]
        selected_diets = [d for d, v in diet_vars.items() if v.get()]
        if not ingredients:
            tk.messagebox.showerror(app.tr("missing"), "Enter at least one ingredient.")
            return

        app.last_ingredients = ", ".join(ingredients)
        app.last_diets = selected_diets
        save_history(app.last_ingredients)

        for tab in tab_control.tabs():
            tab_control.forget(tab)

        loading = ttk.Label(app.main, text=app.tr("searching"), bootstyle="info")
        loading.pack()
        app.root.update_idletasks()

        results = find_by_ingredients(ingredients, number=15)
        random.shuffle(results)

        found = 0
        selected_meal_type = meal_type_filter.get().lower()
        tr_any = app.tr("any").lower()

        for r in results:
            if found >= 5:
                break

            info = get_recipe_info(r['id'])
            if not info:
                continue
            if selected_diets and not matches_diet(info, selected_diets):
                continue
            if not (time_min.get() <= info.get('readyInMinutes', 0) <= time_max.get()):
                continue
            if selected_meal_type != tr_any and selected_meal_type not in info.get("dishTypes", []):
                continue

            app.display_recipe_tab(tab_control, r, info)
            found += 1

        loading.destroy()

        if found == 0:
            tk.messagebox.showinfo(app.tr("no_results"), "No matching recipes found.")

def update_time_label(var, label, v):
    var.set(int(float(v)))
    label.config(text=f"{var.get()} min")
