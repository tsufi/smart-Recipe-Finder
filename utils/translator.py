#utils/translator.py
import json
import os

class Translator:
    def __init__(self, language="en"):
        self.language = language
        self.translations = {}
        self.load_language(language)

    def load_language(self, language):
        self.language = language
        path = os.path.join("lang", f"{language}.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                self.translations = json.load(f)
        else:
            self.translations = {}

    def _(self, key):
        return self.translations.get(key, key)
