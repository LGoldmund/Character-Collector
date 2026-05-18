import os
import tkinter as tk
import subprocess
import time
from tkinter import messagebox, simpledialog, filedialog
from manager import SeriesManager, Character
from PIL import Image, ImageTk


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Character Collector")
        self.root.geometry("726x800")
        self.root.resizable(False, True)

        try:
            icon_image = tk.PhotoImage(file="assets/app_icon.png")
            self.root.iconphoto(True, icon_image)
        except Exception as e:
            print(f"Could not load app icon: {e}")

        self.manager = SeriesManager()
        self.current_series = None

        self.left_frame = tk.Frame(self.root, width=200, bg="#282B32")
        self.left_frame.pack(side="left", fill="y")

        self.right_frame = tk.Frame(self.root, bg="#282B32")
        self.right_frame.pack(side="right", expand=True, fill="both")

        self.setup_sidebar()
        self.setup_main_area()


    def setup_sidebar(self):
        tk.Label(self.left_frame,
                 text="Series",
                 font=("Arial", 16, "bold"),
                 bg="#282B32", anchor="w").pack(side="top", fill="x", pady=16, padx=24, anchor="w")

        self.series_listbox = tk.Listbox(
            self.left_frame,
            bg="#1E1E1E",
            fg="#FFFFFF",
            selectbackground="#69B2DF",
            selectforeground="#1E1E1E",
            borderwidth=0,
            highlightthickness=0,
            font=("Arial", 16),
            activestyle="none"
        )
        self.series_listbox.pack(padx=(24, 0), fill="both", expand=True)
        self.series_listbox.bind('<<ListboxSelect>>', self.on_series_select)
        self.series_listbox.bind("<Button-2>", self.show_series_context_menu)
        self.series_listbox.bind("<Button-3>", self.show_series_context_menu)

        tk.Button(
            self.left_frame,
            text="Add Series",
            activebackground="#3b3e45",
            bg="#282B32",
            highlightthickness=0,
            bd=0,
            command=self.add_series_popup).pack(side="bottom", fill="x", padx=(24, 0), pady=16)
        self.refresh_sidebar()


    def show_series_context_menu(self, event):
        index = self.series_listbox.nearest(event.y)
        if index < 0: return

        self.series_listbox.selection_clear(0, tk.END)
        self.series_listbox.selection_set(index)
        series_name = self.series_listbox.get(index)

        menu = tk.Menu(self.root, tearoff=0, bg="#282B32")
        menu.add_command(label=f"Rename '{series_name}'",
                         command=lambda: self.rename_series_popup(series_name))
        menu.add_separator()
        menu.add_command(label="Delete",
                         command=lambda: self.delete_series_logic(series_name))

        menu.post(event.x_root, event.y_root)


    def delete_series_logic(self, series_name):
        confirm = messagebox.askyesno("Delete Series",
                                      f"Are you sure you want to delete {series_name}? This action cannot be undone.")
        if confirm:
            self.manager.delete_series(series_name)
            self.current_series = None
            self.refresh_sidebar()
            self.refresh_character_list()


    def rename_series_popup(self, old_name):
        new_name = simpledialog.askstring("Rename Series", f"Enter new series name: {old_name}")
        if new_name and new_name != old_name:
            if self.manager.rename_series(old_name, new_name):
                self.current_series = new_name
                self.refresh_sidebar()
                self.refresh_character_list()
            else:
                messagebox.showerror("Rename Series Error", f"Series name {old_name} already exists.")


    def setup_main_area(self):
        self.header_label = tk.Label(
            self.right_frame,
            text="Select a Series",
            font=("Arial", 16, "bold"),
            bg="#282B32",
            fg="white",
            anchor="w"
        )
        self.header_label.pack(side="top", fill="x", pady=16, padx=24, anchor="w")

        self.add_btn = tk.Button(
            self.right_frame,
            text="Add Character",
            activebackground="#3b3e45",
            bg="#282B32",
            highlightthickness=0,
            bd=0,
            command=self.add_character_popup,
            state="disabled",
        )
        self.add_btn.pack(side="bottom", fill="x", padx=24, pady=16)

        self.canvas = tk.Canvas(self.right_frame, bg="#1E1E1E", highlightthickness=0)
        self.canvas.pack(side="top", fill="both", expand=True, padx=24)

        self.card_container = tk.Frame(self.canvas, bg="#1E1E1E")
        self.canvas_window = self.canvas.create_window((0, 0), window=self.card_container, anchor="nw")
        self.card_container.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)


    def _on_mousewheel(self, event):
        if self.canvas.yview() != (0.0, 1.0):
            self.canvas.yview_scroll(int(-1 * event.delta), "units")


    def on_series_select(self, event):
        selection = self.series_listbox.curselection()
        if selection:
            index = selection[0]
            self.current_series = self.series_listbox.get(index)
            self.refresh_character_list()


    def refresh_character_list(self):
        for widget in self.card_container.winfo_children():
            widget.destroy()

        self.canvas.yview_moveto(0)
        self.canvas.configure(scrollregion=(0, 0, 0, 0))

        if not self.current_series:
            return

        self.header_label.config(text=f"Characters of {self.current_series}")
        self.add_btn.config(state="normal")

        characters = self.manager.get_character_for_series(self.current_series)

        characters.sort(key=lambda x: x.get('group', 'Unknown'))

        current_group = None
        current_row = 0
        current_col = 0

        for char in characters:
            char_group = char.get('group', 'Unknown')

            if char_group != current_group:
                current_group = char_group

                if current_col != 0:
                    current_row += 1

                group_title = tk.Label(
                    self.card_container,
                    text=f"{current_group}",
                    font=("Arial", 14, "bold"),
                    bg="#1E1E1E",
                    fg="#69B2DF",
                    padx=16
                )
                group_title.grid(
                    row=current_row,
                    column=0,
                    columnspan=3,
                    sticky="w",
                    pady=8
                )

                current_row += 1
                current_col = 0

            self.create_character_card(self.card_container, char, current_row, current_col)

            current_col += 1
            if current_col > 2:
                current_col = 0
                current_row += 1


    def capture_screenshot_to_assets(self, popup_window):
        if popup_window and popup_window.winfo_exists():
            popup_window.transient(self.root)

        self.root.withdraw()
        time.sleep(0.25)

        try:
            filename = f"snip_{int(time.time())}.png"
            local_path = os.path.join(self.manager.image_folder, filename)
            subprocess.run(["screencapture", "-i", local_path])
            self.root.deiconify()

            if popup_window and popup_window.winfo_exists():
                popup_window.lift()
                popup_window.focus_force()
                popup_window.grab_set()
                popup_window.grab_release()

            if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
                return local_path
            return None

        except Exception as e:
            self.root.deiconify()
            if popup_window and popup_window.winfo_exists():
                popup_window.lift()
                popup_window.focus_force()
            print(f"Screenshot feature failed: {e}")
            return None

    def create_character_card(self, parent, char_data, r, c):
        card = tk.Frame(parent, bd=0, bg="#282B32", pady=8, padx=16)
        card.grid(row=r, column=c, padx=(16, 0), pady=8, sticky="nsew")

        char_menu = tk.Menu(self.root, tearoff=0, bg="#3b3e45", fg="white")
        char_menu.add_command(label="Edit", command=lambda: self.edit_character(char_data))
        char_menu.add_command(label="Delete", command=lambda: self.delete_character(char_data))

        def show_menu(event):
            char_menu.post(event.x_root, event.y_root)

        card.bind("<Button-2>", show_menu)
        card.bind("<Button-3>", show_menu)
        for child in card.winfo_children():
            child.bind("<Button-2>", show_menu)
            child.bind("<Button-3>", show_menu)

        img_path = char_data.get('image', '')

        if os.path.exists(img_path):
            img = Image.open(img_path)
        else:
            img = Image.new("RGB", (100, 100), "grey")

        img = img.resize((100, 100), Image.Resampling.LANCZOS)
        tk_img = ImageTk.PhotoImage(img)

        img_label = tk.Label(card, image=tk_img)
        img_label.image = tk_img
        img_label.pack()

        tk.Label(card,
                 text=char_data['name'],
                 font=("Arial", 14, "bold"),
                 bg="#282B32",
                 fg="white",
                 wraplength=98,
                 justify="center").pack(pady=(5, 0))
        tk.Label(card,
                 text=char_data['title'],
                 font=("Arial", 12, "italic"),
                 bg="#282B32",
                 fg="white",
                 wraplength=98,
                 justify="center").pack()

        card.bind("<MouseWheel>", self._on_mousewheel)
        for child in card.winfo_children():
            child.bind("<MouseWheel>", self._on_mousewheel)


    def add_series_popup(self):
        name = simpledialog.askstring("Add Series", "Add the title of the series: ")
        if name:
            if self.manager.add_series(name):
                self.refresh_sidebar()
            else:
                messagebox.showwarning("Warning", "This series already exists!")


    def refresh_sidebar(self):
        self.series_listbox.delete(0, tk.END)
        for name in self.manager.get_series_names():
            self.series_listbox.insert(tk.END, name)


    def add_character_popup(self):
        popup = tk.Toplevel(self.root)
        popup.title("Add new character")
        popup.geometry("300x400")

        def resize_window():
            popup.update_idletasks()
            popup.geometry(f"300x{popup.winfo_reqheight()}")

        tk.Label(popup, text="Name").pack(pady=(16, 8))
        name_entry = tk.Entry(popup, bg="gray30", fg="white")
        name_entry.pack()

        tk.Label(popup, text="Class/Group").pack(pady=(16, 8))
        group_entry = tk.Entry(popup, bg="gray30", fg="white")
        group_entry.pack()

        tk.Label(popup, text="Title/Extra Info").pack(pady=(16, 8))
        title_entry = tk.Entry(popup, bg="gray30", fg="white")
        title_entry.pack()

        image_path_var = tk.StringVar(value="Upload an image or make a screenshot directly. "
                                            "Upload square images for best experience.")
        tk.Label(popup, textvariable=image_path_var, font=("Arial", 12, "italic"), wraplength=200).pack(pady=(16, 8))

        def pick_image():
            file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg")])
            if file_path:
                image_path_var.set(file_path)
            resize_window()

        tk.Button(popup, text="Upload image", command=pick_image).pack(pady=8)

        def trigger_snip():
            saved_path = self.capture_screenshot_to_assets(popup)
            if saved_path:
                image_path_var.set(saved_path)
            resize_window()

        tk.Button(popup, text="Make a screenshot", command=trigger_snip).pack(pady=8)

        def save_character():
            name = name_entry.get()
            group = group_entry.get()
            title = title_entry.get()
            path = image_path_var.get()

            if path.startswith("Upload an image"):
                path = ""

            if name and self.current_series:
                new_char = Character(name, group, title, path)
                self.manager.add_character(self.current_series, new_char)
                popup.destroy()
                self.refresh_character_list()
            else:
                messagebox.showerror("error", "name and series selection required.")

        tk.Button(popup, text="Save character", fg="black", command=save_character).pack(pady=(8, 24))

        resize_window()


    def delete_character(self, char_data):
        confirm = messagebox.askyesno("Delete Character",
                                      f"Are you sure you want to delete {char_data['name']}? This cannot be undone.")
        if confirm:
            self.manager.delete_character(self.current_series, char_data['name'])
            self.refresh_character_list()


    def edit_character(self, char_data):
        old_name = char_data['name']
        popup = tk.Toplevel(self.root)
        popup.title(f"Edit {char_data['name']}")
        popup.geometry("300x400")

        tk.Label(popup, text="Name").pack(pady=(16, 8))
        name_entry = tk.Entry(popup)
        name_entry.insert(0, char_data['name'])
        name_entry.pack()

        tk.Label(popup, text="Group").pack(pady=(16, 8))
        group_entry = tk.Entry(popup)
        group_entry.insert(0, char_data.get('group', ''))
        group_entry.pack()

        tk.Label(popup, text="Title").pack(pady=8)
        title_entry = tk.Entry(popup)
        title_entry.insert(0, char_data.get('title', ''))
        title_entry.pack()

        current_full_path = char_data.get('image', '')
        image_path_var = tk.StringVar(value=current_full_path)

        filename_only = os.path.basename(current_full_path) if current_full_path else "No image selected"
        display_label = tk.Label(popup, text=f"Current image: {filename_only}", font=("Arial", 12, "italic"), wraplength=200)
        display_label.pack(pady=(16, 8))

        def resize_window():
            popup.update_idletasks()
            popup.geometry(f"300x{popup.winfo_reqheight()}")

        def change_image_upload():
            file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg")])
            if file_path:
                image_path_var.set(file_path)
                display_label.config(text=f"New: {os.path.basename(file_path)}")
                resize_window()

        tk.Button(popup, text="Upload image", command=change_image_upload).pack(pady=8)

        def change_image_snip():
            saved_path = self.capture_screenshot_to_assets(popup)
            if saved_path:
                image_path_var.set(saved_path)
                display_label.config(text=f"New: {os.path.basename(saved_path)}")
                resize_window()

        tk.Button(popup, text="Make a screenshot", command=change_image_snip).pack(pady=8)

        def save_changes():
            update_data = {
                "name": name_entry.get(),
                "group": group_entry.get(),
                "title": title_entry.get(),
                "image": image_path_var.get()
            }
            success = self.manager.update_character(self.current_series, old_name, update_data)
            if success:
                popup.destroy()
                self.refresh_character_list()
            else:
                messagebox.showerror("error", "name update failed")

        tk.Button(popup, text="Save changes", command=save_changes).pack(pady=(8, 24))

        resize_window()


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
