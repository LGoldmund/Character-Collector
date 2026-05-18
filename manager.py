import shutil
import os
import json
import time

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
    def __init__(self):
        self.database_dir, self.image_folder = self.get_save_directory()
        self.json_path = os.path.join(self.database_dir, "data.json")

        if not os.path.exists(self.image_folder):
            os.makedirs(self.image_folder)

        self.data = self.load_data()


    def get_save_directory(self):
        base_dir = os.path.expanduser('~/Library/Application Support/Character Collector')
        image_dir = os.path.join(base_dir, 'character_images')
        os.makedirs(image_dir, exist_ok=True)
        return base_dir, image_dir


    def load_data(self):
        if not os.path.exists(self.json_path):
            return {}
        try:
            with open(self.json_path, "r") as f:
                raw_data = json.load(f)

                for series_name in raw_data:
                    for char in raw_data[series_name]:
                        img_path = char.get("image", "")
                        if img_path and not img_path.startswith("/"):
                            char["image"] = os.path.normpath(os.path.join(self.database_dir, img_path))

                return raw_data
        except (json.JSONDecodeError, IOError):
            return {}


    def save_data(self):
        try:
            clean_data = {}

            for series_name, character_list in self.data.items():
                clean_data[series_name] = []
                for char in character_list:
                    char_copy = char.copy()
                    img_path = char_copy.get("image", "")

                    if img_path and img_path.startswith("/"):
                        char_copy["image"] = os.path.relpath(img_path, self.database_dir)

                    clean_data[series_name].append(char_copy)

            with open(self.json_path, "w") as f:
                json.dump(clean_data, f, indent=4)
        except IOError as e:
            print(f"Error saving database: {e}")


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

            if original_path and os.path.exists(original_path) and os.path.isfile(original_path):
                file_name = f"{int(time.time())}_{os.path.basename(original_path)}"
                new_local_path = os.path.join(self.image_folder, file_name)

                current_file_dir = os.path.abspath(os.path.dirname(original_path))
                target_file_dir = os.path.abspath(self.image_folder)

                if current_file_dir != target_file_dir:
                    try:
                        shutil.copy2(original_path, new_local_path)
                        character_obj.image_path = new_local_path
                    except Exception as e:
                        print(f"Could not copy image {original_path}: {e}")
                else:
                    character_obj.image_path = new_local_path

            else:
                character_obj.image_path = ""

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
            for char in self.data[series_name]:
                if char["name"] == char_name:
                    img_path = char.get("image")
                    if img_path and os.path.exists(img_path):
                        try: os.remove(img_path)
                        except Exception as e:
                            print(f"Could not delete image {img_path}: {e}")
                    break

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
                    new_path = update_data.get("image", "")

                    if new_path and os.path.exists(new_path) and os.path.isfile(new_path):
                        file_name = os.path.basename(new_path)
                        new_local_path = os.path.join(self.image_folder, file_name)

                        current_file_dir = os.path.abspath(os.path.dirname(new_path))
                        target_file_dir = os.path.abspath(self.image_folder)

                        if current_file_dir != target_file_dir:
                            try:
                                old_img_path = char.get("image")

                                if old_img_path and os.path.exists(old_img_path) and os.path.isfile(old_img_path):
                                    try: os.remove(old_img_path)
                                    except Exception as remove_error:
                                        print(f"Could not delete old image {old_img_path}: {remove_error}")

                                shutil.copy2(new_path, new_local_path)
                                update_data["image"] = new_local_path

                            except Exception as e:
                                print(f"Could not copy image {new_path}: {e}")

                        else:
                            update_data["image"] = new_local_path

                    self.data[series_name][i] = update_data
                    self.save_data()
                    return True
        return False


    def delete_series(self, series_name):
        if series_name in self.data:
            for char in self.data[series_name]:
                img_path = char.get("image")
                if img_path and os.path.exists(img_path):
                    try: os.remove(img_path)
                    except Exception as e:
                        print(f"Could not delete image {img_path}: {e}")

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
