import tkinter as tk
from tkinter import ttk, messagebox

from dialog_base import DialogBase
from rpmodels import *

class ConstraintTab(ttk.Frame):
    def __init__(self, app, tab):
        super().__init__(app.notebook)
        self.app = app
        self.tab = tab

    def create(self):
        container = ttk.Frame(self.tab, padding=10)
        container.pack(fill="both", expand=True)

        ttk.Label(container, text="Additional Constraints", font=("TkDefaultFont", 16, "bold")).pack(anchor="w", pady=(0, 5) )

        ttk.Label(container, text=("These are hard constraints used by planners.")).pack(anchor="w", pady=(0, 10))

        frame = ttk.Frame(container)
        frame.pack(fill="both", expand=True)

        self.constraint_tree = ttk.Treeview(frame, columns=("type", "person1", "person2", "room1", "room2"), show="headings")

        self.constraint_tree.heading("type", text="Constraint")
        self.constraint_tree.heading("person1", text="Person X")
        self.constraint_tree.heading("person2", text="Person Y")
        self.constraint_tree.heading("room1", text="Room A")
        self.constraint_tree.heading("room2", text="Room B")

        self.constraint_tree.column("type", width=200)
        self.constraint_tree.column("person1", width=220)
        self.constraint_tree.column("person2", width=220)
        self.constraint_tree.column("room1", width=220)
        self.constraint_tree.column("room2", width=220)

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.constraint_tree.yview)

        self.constraint_tree.configure(yscrollcommand=scrollbar.set)

        self.constraint_tree.pack(side="left", fill="both", expand=True)

        scrollbar.pack(side="right", fill="y")

        self.constraint_tree.bind("<Double-1>", lambda e: self.edit_selected_constraint())

        buttons = ttk.Frame(container)
        buttons.pack(fill="x", pady=(10, 0))

        ttk.Button(buttons, text="Add", command=self.add_constraint).pack(side="left", padx=3)

        ttk.Button(buttons, text="Edit", command=self.edit_selected_constraint).pack(side="left", padx=3)

        ttk.Button(buttons, text="Remove", command=self.remove_selected_constraint).pack(side="left", padx=3)

        ttk.Button(buttons, text="Load...", command=self.app.load_constraints).pack(side="right", padx=3)

        ttk.Button(buttons, text="Save...", command=self.app.save_constraints).pack(side="right", padx=3)

        self.refresh_constraints()

    def refresh_constraints(self):
        if not hasattr(self, "constraint_tree"):
            return

        for item in self.constraint_tree.get_children():
            self.constraint_tree.delete(item)

        for c in self.app.appdata.constraints:
            if c.type == "same":
                values = ("Persons X and Y to the same room", c.person1, c.person2, "", "")
            elif c.type == "different":
                values = ("Persons X and Y to different rooms", c.person1, c.person2, "", "")
            elif c.type == "to_room":
                values = ("Person X to room A", c.person, "", c.room, "")
            elif c.type == "not_to_room":
                values = ("Person X not to room A", c.person, "", c.room, "")
            elif c.type == "male":
                values = ("Room A to males", "", "", c.room, "")
            elif c.type == "female":
                values = ("Room A to females", "", "", c.room, "")
            elif c.type == "same_gender":
                values = ("Rooms A and B to the same gender", "", "", c.room1, c.room2)
            else:
                values = (c.type, "", "", "")

            self.constraint_tree.insert("", "end", values=values )

    def add_constraint(self):
        if not self.app.appdata.people:
            messagebox.showinfo("No People", "Add people before creating constraints.")
            return

        dialog = ConstraintDialog(
            self,
            "Add Constraint",
            [p.name for p in self.app.appdata.people],
            [r.name for r in self.app.appdata.rooms]
        )

        if dialog.result is None:
            return

        if any(c == dialog.result for c in self.app.appdata.constraints):
            messagebox.showerror("Duplicate", "This constraint already exists.")
            return

        self.app.appdata.constraints.append(dialog.result)

        self.refresh_constraints()

    def edit_selected_constraint(self):
        selection = self.constraint_tree.selection()

        if not selection:
            messagebox.showinfo("No Selection", "Select a constraint first.")
            return

        index = self.constraint_tree.index(selection[0])

        dialog = ConstraintDialog(
            self,
            "Edit Constraint",
            [p.name for p in self.app.appdata.people],
            [r.name for r in self.app.appdata.rooms],
            self.app.appdata.constraints[index]
        )

        if dialog.result is None:
            return

        self.app.appdata.constraints[index] = dialog.result

        self.refresh_constraints()

    def remove_selected_constraint(self):
        selection = self.constraint_tree.selection()

        if not selection:
            messagebox.showinfo("No Selection", "Select a constraint first.")
            return

        index = self.constraint_tree.index(selection[0])

        del self.app.appdata.constraints[index]

        self.refresh_constraints()


class ConstraintDialog(DialogBase):
    TYPES = {
        "Persons X and Y to the same room": "same",
        "Persons X and Y to different rooms": "different",
        "Person X to room A": "to_room",
        "Person X not to room A": "not_to_room",
        "Room A to males": "male",
        "Room A to females": "female",
        "Rooms A and B to the same gender": "same_gender",
    }

    def __init__(self, parent, title, people, rooms, constraint=None):
        super().__init__(parent, title)

        self.people = people
        self.rooms = rooms

        frame = ttk.Frame(self, padding=15)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Type:").grid(row=0, column=0, sticky="w", pady=5)

        reverse = {value: key for key, value in self.TYPES.items()}

        initial = reverse.get(constraint.type) if constraint else "Persons X and Y to the same room"

        self.type_var = tk.StringVar(value=initial)

        combo = ttk.Combobox(frame, textvariable=self.type_var, values=list(self.TYPES.keys()), state="readonly", width=30)
        combo.grid(row=0, column=1, sticky="ew", pady=5)
        combo.bind("<<ComboboxSelected>>", self.update_fields)

        # Person X
        ttk.Label(frame, text="Person X:").grid(row=1, column=0, sticky="w", pady=5)

        self.person1_var = tk.StringVar()

        if constraint:
            self.person1_var.set(constraint.person1 or constraint.person or "")

        self.person1_combo = ttk.Combobox(frame, textvariable=self.person1_var, values=people, state="readonly", width=30)
        self.person1_combo.grid(row=1, column=1, sticky="ew", pady=5)

        # Person Y
        ttk.Label(frame, text="Person Y:").grid(row=2, column=0, sticky="w", pady=5)

        self.person2_var = tk.StringVar()

        if constraint:
            self.person2_var.set(constraint.person2 or "")

        self.person2_combo = ttk.Combobox(frame, textvariable=self.person2_var, values=people, state="readonly", width=30)
        self.person2_combo.grid(row=2, column=1, sticky="ew", pady=5)

        # Room A
        ttk.Label(frame, text="Room A:").grid(row=3, column=0, sticky="w", pady=5)

        self.room1_var = tk.StringVar()

        if constraint:
            self.room1_var.set(constraint.room1 or "")

        self.room1_combo = ttk.Combobox(frame, textvariable=self.room1_var, values=rooms, state="readonly", width=30)
        self.room1_combo.grid(row=3, column=1, sticky="ew", pady=5)

        # Room B
        ttk.Label(frame, text="Room B:").grid(row=4, column=0, sticky="w", pady=5)

        self.room2_var = tk.StringVar()

        if constraint:
            self.room2_var.set(constraint.room2 or "")

        self.room2_combo = ttk.Combobox(frame, textvariable=self.room2_var, values=rooms, state="readonly", width=30)
        self.room2_combo.grid(row=4, column=1, sticky="ew", pady=5)

        buttons = ttk.Frame(frame)
        buttons.grid(row=5, column=0, columnspan=2, sticky="e", pady=(15, 0))

        ttk.Button(buttons, text="Cancel", command=self.cancel).pack(side="right", padx=5)
        ttk.Button(buttons, text="OK", command=self.ok).pack(side="right", padx=5)

        frame.columnconfigure(1, weight=1)

        self.update_fields()

        self.bind("<Escape>", lambda e: self.cancel())

        self.wait_window()

    def update_fields(self, event=None):
        ctype = self.TYPES[self.type_var.get()]

        if ctype in ("same", "different"):
            self.person1_combo.configure(state="readonly")
            self.person2_combo.configure(state="readonly")
            self.room1_combo.configure(state="disabled")
            self.room2_combo.configure(state="disabled")
        elif ctype in ("to_room", "not_to_room"):
            self.person1_combo.configure(state="readonly")
            self.person2_combo.configure(state="disabled")
            self.room1_combo.configure(state="readonly")
            self.room2_combo.configure(state="disabled")
        elif ctype in ("male", "female"):
            self.person1_combo.configure(state="disabled")
            self.person2_combo.configure(state="disabled")
            self.room1_combo.configure(state="readonly")
            self.room2_combo.configure(state="disabled")
        elif ctype in ("same_gender"):
            self.person1_combo.configure(state="disabled")
            self.person2_combo.configure(state="disabled")
            self.room1_combo.configure(state="readonly")
            self.room2_combo.configure(state="readonly")
        else:
            self.person1_combo.configure(state="disabled")
            self.person2_combo.configure(state="disabled")
            self.room1_combo.configure(state="disabled")
            self.room2_combo.configure(state="disabled")

    def ok(self):
        ctype = self.TYPES[self.type_var.get()]

        if ctype in ("same", "different"):
            p1 = self.person1_var.get()
            p2 = self.person2_var.get()

            if not p1 or not p2:
                messagebox.showerror("Invalid", "Both people must be selected.", parent=self)
                return

            if p1 == p2:
                messagebox.showerror("Invalid", "The people must be different.", parent=self)
                return

            self.result = Constraint(type=ctype, person1=p1, person2=p2)
        elif ctype in ("to_room", "not_to_room"):
            person = self.person1_var.get()
            room = self.room1_var.get()

            if not person or not room:
                messagebox.showerror("Invalid", "Select both a person and room.", parent=self)
                return

            self.result = Constraint(type=ctype, person=person, room=room)
        elif ctype in ("male", "female"):
            person = self.person1_var.get()
            room = self.room1_var.get()

            if not room:
                messagebox.showerror("Invalid", "Select a room.", parent=self)
                return

            self.result = Constraint(type=ctype, room=room)
        elif ctype in ("same_gender"):
            room1 = self.room1_var.get()
            room2 = self.room2_var.get()

            if not room1 or not room2:
                messagebox.showerror("Invalid", "Select both rooms.", parent=self)
                return
            if room1==room2:
                messagebox.showerror("Invalid", "The rooms must be different.", parent=self)
                return

            self.result = Constraint(type=ctype, room1=room1, room2=room2)
        else:
            messagebox.showerror("Invalid", "Unknown type", parent=self)
            return

        self.destroy()
