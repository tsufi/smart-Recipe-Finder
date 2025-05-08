#ui/recipe_tab.py
import tkinter as tk
import webbrowser
import requests
from PIL import Image, ImageTk
import io
import json
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from api.nutrition_parse import parse_nutrition_summary
from components.scrollable_frame import ScrollableFrame
from data.storage import save_favorites, get_favorites, save_mealplan, get_mealplan


class RecipeTab:
    def __init__(self, app, notebook, basic_info, full_info, show_close=False):
        self.app = app
        self.full_info = full_info
        self.notebook = notebook
        self.tab = ScrollableFrame(notebook)
        notebook.add(self.tab, text=basic_info.get("title", "Recipe"))


        self._add_header()
        self._add_image()
        self._add_meta()
        self._add_buttons()
        self._add_summary()
        self._add_ingredients()
        self._add_instructions()
        self._add_tools()  # <- inserted here
        self._add_nutrition_section()
        if show_close:
            close_btn = ttk.Button(self.tab, text=self.app.tr("close_tab"), bootstyle="danger", command=self.close_tab)
            close_btn.pack(anchor="ne", padx=10, pady=5)

    def _add_header(self):
        ttk.Label(self.tab.scrollable_frame, text=self.full_info['title'],
                  font=("Segoe UI", 16, "bold")).pack(pady=10)

    def _add_image(self):
        img_frame = ttk.Frame(self.tab.scrollable_frame)
        img_frame.pack(pady=5)

        if 'image' in self.full_info and self.full_info['image']:
            try:
                img_data = requests.get(self.full_info['image'], timeout=5).content
                img = Image.open(io.BytesIO(img_data))
                img.thumbnail((300, 300))
                photo = ImageTk.PhotoImage(img)
                img_label = ttk.Label(img_frame, image=photo)
                img_label.image = photo
                img_label.pack()
            except Exception:
                ttk.Label(img_frame, text=self.app.tr("no_image"), font=("Segoe UI", 10)).pack()
        else:
            ttk.Label(img_frame, text=self.app.tr("no_image"), font=("Segoe UI", 10)).pack()

    def _add_meta(self):
        ready = self.full_info.get("readyInMinutes", "?")
        servings = self.full_info.get("servings", "?")
        meta = f"Ready in {ready} min | Servings: {servings}"
        ttk.Label(self.tab.scrollable_frame, text=meta, font=("Segoe UI", 10)).pack(pady=5)

    def _add_buttons(self):
        btn_frame = ttk.Frame(self.tab.scrollable_frame)
        btn_frame.pack(pady=5)

        ttk.Button(btn_frame, text=self.app.tr("favorite"), command=self.add_to_favorites).pack(side="left", padx=5)
        ttk.Button(btn_frame, text=self.app.tr("meal_plan"), command=self.add_to_mealplan).pack(side="left", padx=5)
        ttk.Button(btn_frame, text=self.app.tr("website"), command=self.open_website).pack(side="left", padx=5)

    def _add_summary(self):
        summary = self.full_info.get("summary", "").replace("<b>", "").replace("</b>", "")
        text = tk.Text(self.tab.scrollable_frame, wrap="word", height=5, bg="#2b2b2b", fg="white", insertbackground="white")
        text.insert("1.0", summary)
        text.config(state="disabled")
        text.pack(fill="both", padx=5, pady=5)

    def _add_ingredients(self):
        ingredients = self.full_info.get("extendedIngredients", [])
        if ingredients:
            ttk.Label(self.tab.scrollable_frame, text=self.app.tr("ingredients"), font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=5)
            text = tk.Text(self.tab.scrollable_frame, height=6, wrap="word", bg="#1e1e1e", fg="lightgreen", insertbackground="white")
            for ing in ingredients:
                line = f"• {ing['original']}\n"
                text.insert("end", line)
            text.config(state="disabled")
            text.pack(fill="x", padx=5, pady=5)

    def _add_instructions(self):
        steps = self.full_info.get("analyzedInstructions", [])
        if steps:
            text = tk.Text(self.tab.scrollable_frame, wrap="word", height=10, bg="#2b2b2b", fg="white", insertbackground="white")
            for s in steps[0]['steps']:
                text.insert("end", f"{s['number']}. {s['step']}\n\n")
            text.config(state="disabled")
            text.pack(fill="both", expand=True, padx=5, pady=5)

    def _add_tools(self):
        try:
            with open("data/tools_map.json", "r", encoding="utf-8") as f:
                tool_map = json.load(f)
        except Exception:
            return

        content = (
            self.full_info.get("summary", "") + " " +
            " ".join(step["step"] for inst in self.full_info.get("analyzedInstructions", []) for step in inst.get("steps", []))
        ).lower()

        found_tools = {tool: url for tool, url in tool_map.items() if tool in content}

        if found_tools:
            ttk.Label(self.tab.scrollable_frame, text=self.app.tr("recommended_tools"), font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=5, pady=(10, 0))
            for name, link in found_tools.items():
                link_label = tk.Label(
                    self.tab.scrollable_frame,
                    text=f"• {name.title()} (Buy on Amazon)",
                    fg="blue",
                    cursor="hand2",
                    font=("Segoe UI", 10, "underline"),
                    bg=self.tab.scrollable_frame["bg"]
                )
                link_label.pack(anchor="w", padx=10)
                link_label.bind("<Button-1>", lambda e, url=link: webbrowser.open_new_tab(url))

    def _add_nutrition_section(self):
        nutrition_data = self.full_info.get("nutrition", {})
        print(f"[DEBUG] Nutrition for {self.full_info.get('title', 'Unknown')}:\n", nutrition_data)

        container = ttk.Frame(self.tab.scrollable_frame)
        container.pack(fill="x", padx=5, pady=5)

        toggle_btn = ttk.Button(container, text=self.app.tr("show_nutrition"), bootstyle="info")
        frame = ttk.Frame(container)
        frame.pack_forget()

        def toggle():
            if frame.winfo_ismapped():
                frame.pack_forget()
                toggle_btn.config(text=self.app.tr("show_nutrition"))
            else:
                frame.pack(fill="x", pady=5)
                toggle_btn.config(text=self.app.tr("hide_nutrition"))

        toggle_btn.config(command=toggle)
        toggle_btn.pack(anchor="w")

        lines = parse_nutrition_summary(nutrition_data)

        if not lines:
            ttk.Label(frame, text=self.app.tr("no_nutrition"), font=("Segoe UI", 10, "italic")).pack(anchor="w")
            return

        for line in lines:
            ttk.Label(frame, text=line).pack(anchor="w")

    def add_to_favorites(self):
        favs = get_favorites()
        if self.full_info['id'] in [f['id'] for f in favs]:
            tk.messagebox.showinfo(self.app.tr("already_added"), "This recipe is already in your favorites.")
            return
        favs.append({'id': self.full_info['id'], 'title': self.full_info['title']})
        save_favorites(favs)
        tk.messagebox.showinfo(self.app.tr("added"), f"'{self.full_info['title']}' added to favorites.")

    def add_to_mealplan(self):
        def confirm():
            day = day_var.get()
            meal = meal_var.get()
            if not day or not meal:
                tk.messagebox.showerror(self.app.tr("missing_info"), "Please select both day and meal type.")
                return

            plan = get_mealplan()
            plan.append({
                "title": self.full_info['title'],
                "id": self.full_info['id'],
                "day": day,
                "meal": meal,
                "readyInMinutes": self.full_info.get('readyInMinutes'),
                "servings": self.full_info.get('servings')
            })
            save_mealplan(plan)
            tk.messagebox.showinfo(self.app.tr("added"), f"Added to {meal} on {day}.")
            popup.destroy()

        popup = tk.Toplevel()
        popup.title("Add to Meal Plan")
        popup.geometry("300x180")
        popup.resizable(False, False)

        ttk.Label(popup, text=self.app.tr("select_day")).pack(pady=5)
        day_var = tk.StringVar()
        ttk.Combobox(popup, textvariable=day_var, values=[
            "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
        ]).pack()

        ttk.Label(popup, text=self.app.tr("select_meal")).pack(pady=5)
        meal_var = tk.StringVar()
        ttk.Combobox(popup, textvariable=meal_var, values=[
            "Breakfast", "Lunch", "Dinner"
        ]).pack()

        ttk.Button(popup, text=self.app.tr("add"), command=confirm, bootstyle="success").pack(pady=10)


    def open_website(self):
        url = self.full_info.get("sourceUrl", "#")
        webbrowser.open(url)

    def close_tab(self):
        self.notebook.forget(self.tab)