import tkinter as tk
from tkinter import ttk, messagebox

from dialog_base import DialogBase
from rpmodels import *

class RoomTab(ttk.Frame):
    def __init__(self, app, tab):
        super().__init__(app.notebook)
        self.app = app
        self.tab = tab

    def create(self):
        container = ttk.Frame(self.tab, padding=10)
        container.pack(fill="both", expand=True)

        ttk.Label(container, text="Rooms", font=("TkDefaultFont", 16, "bold")).pack(anchor="w", pady=(0, 10))

        table_frame = ttk.Frame(container)
        table_frame.pack(fill="both", expand=True)

        self.room_tree = ttk.Treeview(table_frame, columns=("name", "size"), show="headings")

        self.room_tree.heading("name", text="Room Name")
        self.room_tree.heading("size", text="Capacity")

        self.room_tree.column("name", width=400)
        self.room_tree.column("size", width=150, anchor="center")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.room_tree.yview)

        self.room_tree.configure(yscrollcommand=scrollbar.set)

        self.room_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.room_tree.bind("<Double-1>", lambda e: self.edit_selected_room())

        buttons = ttk.Frame(container)
        buttons.pack(fill="x", pady=(10, 0))

        ttk.Button(buttons, text="Add Room", command=self.add_room).pack(side="left", padx=3)
        ttk.Button(buttons, text="Edit", command=self.edit_selected_room).pack(side="left", padx=3)
        ttk.Button(buttons, text="Remove", command=self.remove_selected_room).pack(side="left", padx=3)
        ttk.Button(buttons, text="Clear All", command=self.clear_rooms).pack(side="left", padx=3)

        ttk.Button(buttons, text="Load...", command=self.app.load_rooms).pack(side="right", padx=3)
        ttk.Button(buttons, text="Save...", command=self.app.save_rooms).pack(side="right", padx=3)

        self.refresh_rooms()



    def refresh_rooms(self):
        for item in self.room_tree.get_children():
            self.room_tree.delete(item)

        for room in self.app.appdata.rooms:
            self.room_tree.insert("", "end", values=(room.name, room.size))

    def add_room(self):
        dialog = RoomDialog(self, "Add Room")

        if dialog.result is None:
            return

        name, size = dialog.result

        if any(r.name == name for r in self.app.appdata.rooms):
            messagebox.showerror("Duplicate", f"Room '{name}' already exists.")
            return

        self.app.appdata.rooms.append(Room(name, size))

        self.refresh_rooms()

    def edit_selected_room(self):
        selection = self.room_tree.selection()

        if not selection:
            messagebox.showinfo("No Selection", "Select a room first.")
            return

        index = self.room_tree.index(selection[0])

        room = self.app.appdata.rooms[index]

        dialog = RoomDialog(self, "Edit Room", room.name, room.size)

        if dialog.result is None:
            return

        new_name, new_size = dialog.result

        for i, other in enumerate(self.app.appdata.rooms):
            if i != index and other.name == new_name:
                messagebox.showerror("Duplicate", f"Room '{new_name}' already exists.")
                return

        old_name = room.name

        room.name = new_name
        room.size = new_size

        for constraint in self.app.appdata.constraints:
            if (
                constraint.type in
                ("to_room", "not_to_room")
                and constraint.room == old_name
            ):
                constraint.room = new_name

        self.refresh_rooms()
        self.refresh_constraints()

    def remove_selected_room(self):
        selection = self.room_tree.selection()

        if not selection:
            messagebox.showinfo("No Selection", "Select a room first.")
            return

        index = self.room_tree.index(selection[0])

        room_name = self.app.appdata.rooms[index].name

        if not messagebox.askyesno("Remove Room", f"Remove room '{room_name}'?"):
            return

        del self.app.appdata.rooms[index]

        self.app.appdata.constraints = [
            c for c in self.app.appdata.constraints
            if not (
                c.type in ("to_room", "not_to_room")
                and c.room == room_name
            )
        ]

        self.refresh_rooms()
        self.refresh_constraints()

    def clear_rooms(self):
        if not self.app.appdata.rooms:
            return

        if not messagebox.askyesno("Clear Rooms", "Remove all rooms?"):
            return

        self.app.appdata.rooms.clear()

        self.constraints = [
            c for c in self.constraints
            if c.type not in ("to_room", "not_to_room")
        ]

        self.refresh_rooms()
        self.refresh_constraints()




class RoomDialog(DialogBase):
    def __init__(self, parent, title, name="", size=4):
        super().__init__(parent, title)

        frame = ttk.Frame(self, padding=15)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Room name:").grid(row=0, column=0, sticky="w", pady=5)

        self.name_var = tk.StringVar(value=name)

        name_entry = ttk.Entry(frame, textvariable=self.name_var, width=40)

        name_entry.grid(row=0, column=1, sticky="ew", pady=5)

        ttk.Label(frame, text="Capacity:").grid(row=1, column=0, sticky="w",pady=5)

        self.size_var = tk.StringVar(value=str(size))

        ttk.Entry(frame, textvariable=self.size_var, width=10).grid(row=1, column=1, sticky="w", pady=5)

        buttons = ttk.Frame(frame)
        buttons.grid(row=2, column=0, columnspan=2, sticky="e", pady=(15, 0))

        ttk.Button(buttons, text="Cancel", command=self.cancel).pack(side="right", padx=5)

        ttk.Button(buttons, text="OK", command=self.ok).pack(side="right", padx=5)

        frame.columnconfigure(1, weight=1)

        name_entry.focus_set()

        self.bind("<Return>", lambda e: self.ok())
        self.bind("<Escape>", lambda e: self.cancel())

        self.wait_window()

    def ok(self):
        name = self.name_var.get().strip()

        if not name:
            messagebox.showerror("Invalid", "Room name cannot be empty.", parent=self)
            return

        try:
            size = int(self.size_var.get())
        except ValueError:
            messagebox.showerror("Invalid", "Capacity must be an integer.", parent=self)
            return

        if size <= 0:
            messagebox.showerror("Invalid", "Capacity must be greater than zero.", parent=self)
            return

        self.result = (name, size)

        self.destroy()
