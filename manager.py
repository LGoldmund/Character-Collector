import shutil
import os
import json


class Character:
    def __init__(self, name, group, title, image_path):
        self.name = name
        self.group = group
        self.title = title
        self.image_path = image_path


    def to_dict(self):
        return {
            "name": self.name,
            "group": self.group,
            "title": self.title,
            "image": self.image_path
        }

class SeriesManager:
    def __init__(self, storage_file="data.JSON"):
        self.storage_file = storage_file
        self.image_folder = "assets/characters"
        self.data = self.load_data()

        if not os.path.exists(self.image_folder):
            os.makedirs(self.image_folder)


    def load_data(self):
        if not os.path.exists(self.storage_file):
            return {}
        try:
            with open(self.storage_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}


    def save_data(self):
        with open(self.storage_file, "w") as f:
            json.dump(self.data, f, indent=4)


    def add_series(self, series_name):
        clean_name = series_name.strip()
        if clean_name and clean_name not in self.data:
            self.data[clean_name] = []
            self.save_data()
            return True
        return False


    def add_character(self, series_name, character_obj):
        if series_name in self.data:
            original_path = character_obj.image_path

            if os.path.exists(original_path):
                file_name = os.path.basename(original_path)
                new_local_path = os.path.join(self.image_folder, file_name)

                if os.path.abspath(original_path) != os.path.abspath(new_local_path):
                    shutil.copy2(original_path, new_local_path)

                character_obj.image_path = new_local_path

            self.data[series_name].append(character_obj.to_dict())
            self.save_data()
            return True
        return False


    def get_series_names(self):
        return sorted(list(self.data.keys()))


    def get_character_for_series(self, series_name):
        characters = self.data.get(series_name, [])
        sorted_characters = sorted(characters, key=lambda x: x["title"].lower())
        return sorted_characters


    def delete_character(self, series_name, char_name):
        if series_name in self.data:
            self.data[series_name] = [
                char for char in self.data[series_name]
                if char["name"] != char_name
            ]
            self.save_data()
            return True
        return False


    def update_character(self, series_name, old_name, update_data):
        if series_name in self.data:
            for i, char in enumerate(self.data[series_name]):
                if char["name"] == old_name:
                    self.data[series_name][i] = update_data
                    self.save_data()
                    return True
        return False


    def delete_series(self, series_name):
        if series_name in self.data:
            del self.data[series_name]
            self.save_data()
            return True
        return False


    def rename_series(self, old_name, new_name):
        if old_name in self.data and new_name not in self.data:
            self.data[new_name] = self.data.pop(old_name)
            self.save_data()
            return True
        return False