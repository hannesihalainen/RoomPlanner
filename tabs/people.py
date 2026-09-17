import tkinter as tk
from tkinter import filedialog, ttk, messagebox

from dialog_base import DialogBase
from rpmodels import *


class PeopleTab(ttk.Frame):
    def __init__(self, app, tab):
        super().__init__(app.notebook)
        self.app = app
        self.tab = tab

    def create(self):
        outer = ttk.Frame(self.tab, padding=10)
        outer.pack(fill="both", expand=True)

        ttk.Label(outer, text="People", font=("TkDefaultFont", 16, "bold")).pack(anchor="w",pady=(0, 10))

        paned = ttk.PanedWindow(outer, orient="horizontal")
        paned.pack(fill="both", expand=True)

        people_frame = ttk.Frame(paned, padding=5)
        wishes_frame = ttk.Frame(paned, padding=5)

        paned.add(people_frame, weight=1)
        paned.add(wishes_frame, weight=2)

        ttk.Label(people_frame, text="People").pack(anchor="w")

        list_frame = ttk.Frame(people_frame)
        list_frame.pack(fill="both", expand=True, pady=5)

        self.people_tree = ttk.Treeview(list_frame, columns=("name", "gender"), show="headings", selectmode="browse")

        self.people_tree.heading("name", text="Name")
        self.people_tree.heading("gender", text="Gender")

        self.people_tree.column("name", width=250)
        self.people_tree.column("gender", width=100, anchor="center")

        scrollbar = ttk.Scrollbar(list_frame,orient="vertical", command=self.people_tree.yview)

        self.people_tree.configure(yscrollcommand=scrollbar.set)

        self.people_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.people_tree.bind("<<TreeviewSelect>>", self.person_selected)
        self.people_tree.bind("<Double-1>", self.toggle_gender)

        buttons = ttk.Frame(people_frame)
        buttons.pack(fill="x")

        ttk.Button(buttons, text="Add", command=self.add_person).pack(side="left", padx=2)

        ttk.Button(buttons, text="Edit", command=self.edit_selected_person).pack(side="left", padx=2)

        ttk.Button(buttons, text="Remove", command=self.remove_selected_person).pack(side="left", padx=2)

        ttk.Button(buttons, text="Clear", command=self.clear_people).pack(side="left", padx=2)

        ttk.Button(buttons, text="Import", command=self.import_people).pack(side="left", padx=2)

        # Wishes
        self.selected_person_label = ttk.Label(wishes_frame, text="Select a person", font=("TkDefaultFont", 13, "bold"))
        self.selected_person_label.pack(anchor="w")

        ttk.Label(wishes_frame, text=(
                "A wish indicates that the person would like "
                "to share a room with another person. "
                "The weight expresses the strength of the wish."
            ),
            wraplength=600
        ).pack(anchor="w", pady=(3, 10))

        wish_frame = ttk.Frame(wishes_frame)
        wish_frame.pack(fill="both", expand=True)

        self.wish_tree = ttk.Treeview(wish_frame, columns=("person", "weight"), show="headings")

        self.wish_tree.heading("person", text="Person")
        self.wish_tree.heading("weight", text="Weight")

        self.wish_tree.column("person", width=250)
        self.wish_tree.column("weight", width=100, anchor="center")

        wish_scrollbar = ttk.Scrollbar(wish_frame, orient="vertical", command=self.wish_tree.yview)

        self.wish_tree.configure(yscrollcommand=wish_scrollbar.set)

        self.wish_tree.pack(side="left", fill="both", expand=True)
        wish_scrollbar.pack(side="right", fill="y")

        self.wish_tree.bind("<Double-1>", lambda e: self.edit_selected_wish())

        wish_buttons = ttk.Frame(wishes_frame)
        wish_buttons.pack(fill="x", pady=(10, 0))

        ttk.Button(wish_buttons, text="Add Wish", command=self.add_wish).pack(side="left", padx=3)

        ttk.Button(wish_buttons, text="Edit", command=self.edit_selected_wish).pack(side="left", padx=3)

        ttk.Button(wish_buttons, text="Remove", command=self.remove_selected_wish).pack(side="left", padx=3)

        bottom = ttk.Frame(outer)
        bottom.pack(fill="x", pady=(10, 0))

        ttk.Button(bottom, text="Load People...", command=self.app.load_people).pack(side="right", padx=3)

        ttk.Button(bottom, text="Save People...", command=self.app.save_people).pack(side="right",padx=3)

        self.refresh_people()

    def refresh_people(self):
        for item in self.people_tree.get_children():
            self.people_tree.delete(item)

        for person in self.app.appdata.people:
            self.people_tree.insert("", "end", values=(person.name, person.gender))

        self.refresh_wishes()

    def toggle_gender(self, event=None):
        selected = self.people_tree.selection()

        if not selected: return

        item_id = selected[0]
        values = self.people_tree.item(item_id, "values")

        if not values: return

        name = values[0]
        current_gender = values[1]

        if current_gender == "M": new_gender = "F"
        else:                     new_gender = "M"

        self.people_tree.item(item_id, values=(name, new_gender))

        self.update_person_gender(name, new_gender)

    def update_person_gender(self, name, gender):
        for person in self.app.appdata.people:
            if person.name == name:
                person.gender = gender
                break

    def add_person(self):
        dialog = PersonDialog(self, "Add Person")

        if dialog.result is None: return

        name, gender = dialog.result

        if any(p.name == name for p in self.app.appdata.people):
            messagebox.showerror("Duplicate", f"Person '{name}' already exists.")
            return

        self.app.appdata.people.append(Person(name, gender))

        self.refresh_people()

        items = self.people_tree.get_children()
        if items:
            self.people_tree.selection_set(items[-1])
            self.people_tree.focus(items[-1])
            self.people_tree.event_generate("<<TreeviewSelect>>")

    def get_selected_person_index(self):
        selection = self.people_tree.selection()

        if not selection:
            return None

        return self.people_tree.get_children().index(selection[0])

    def get_selected_person(self):
        index = self.get_selected_person_index()

        if index is None:
            return None

        return self.app.appdata.people[index]

    def person_selected(self, event=None):
        self.refresh_wishes()

    def refresh_wishes(self):
        for item in self.wish_tree.get_children():
            self.wish_tree.delete(item)

        person = self.get_selected_person()

        if person is None:
            self.selected_person_label.config(text="Select a person")
            return

        self.selected_person_label.config(text=f"Wishes of {person.name}")

        for wish in person.wishes:
            self.wish_tree.insert("", "end", values=(wish.person, wish.weight))

    def edit_selected_person(self):
        index = self.get_selected_person_index()

        if index is None:
            messagebox.showinfo("No Selection", "Select a person first.")
            return

        person = self.app.appdata.people[index]

        dialog = PersonDialog(self, "Edit Person", person.name, person.gender)

        if dialog.result is None:
            return

        new_name, new_gender = dialog.result

        for i, other in enumerate(self.app.appdata.people):
            if i != index and other.name == new_name:
                messagebox.showerror("Duplicate", f"Person '{new_name}' already exists.")
                return

        old_name = person.name
        person.name = new_name
        person.gender = new_gender

        # Update wishes.
        for p in self.app.appdata.people:
            for wish in p.wishes:
                if wish.person == old_name:
                    wish.person = new_name

        # Update constraints.
        for constraint in self.app.appdata.constraints:
            if constraint.type in ("same", "different"):
                if constraint.person1 == old_name:
                    constraint.person1 = new_name

                if constraint.person2 == old_name:
                    constraint.person2 = new_name

            elif constraint.type in ("to_room", "not_to_room"):
                if constraint.person == old_name:
                    constraint.person = new_name

        self.refresh_people()
        self.app.refresh_constraints()

    def remove_selected_person(self):
        index = self.get_selected_person_index()

        if index is None:
            messagebox.showinfo("No Selection", "Select a person first.")
            return

        name = self.app.appdata.people[index].name

        if not messagebox.askyesno("Remove Person", f"Remove '{name}'?"):
            return

        del self.app.appdata.people[index]

        # Remove wishes pointing to the deleted person.
        for person in self.app.appdata.people:
            person.wishes = [wish for wish in person.wishes if wish.person != name]

        # Remove constraints involving them.
        self.app.appdata.constraints = [
            c
            for c in self.app.appdata.constraints
            if not ((c.type in ("same", "different") and (c.person1 == name or c.person2 == name )) or ( c.type in ( "to_room", "not_to_room") and c.person == name))
        ]

        self.refresh_people()
        self.app.refresh_constraints()

    def clear_people(self):
        if not self.app.appdata.people:
            return

        if not messagebox.askyesno("Clear People", "Remove all people, wishes, and person constraints?"):
            return

        self.app.appdata.people.clear()

        self.app.appdata.constraints = [c for c in self.app.appdata.constraints if c.type not in ("same", "different", "to_room", "not_to_room")]

        self.refresh_people()
        self.app.refresh_constraints()

    def import_people(self):

        filename = filedialog.askopenfilename(
            title="Import people",
            filetypes=[
                ("All files", "*.*")
            ]
        )
        if not filename: return

        try:
            self.app.appdata.import_people(filename)
            self.refresh_people()
        except Exception as e:
            messagebox.showerror("Import Error", str(e))

    def add_wish(self):
        person = self.get_selected_person()

        if person is None:
            messagebox.showinfo("No Person", "Select a person first.")
            return

        possible = [p.name for p in self.app.appdata.people if p.name != person.name]

        if not possible:
            return

        dialog = WishDialog(self, "Add Wish", possible)

        if dialog.result is None:
            return

        wish_person, weight = dialog.result

        if any(w.person == wish_person for w in person.wishes):
            messagebox.showerror("Duplicate", "This wish already exists.")
            return

        person.wishes.append(Wish(wish_person, weight))

        self.refresh_wishes()

    def edit_selected_wish(self):
        person = self.get_selected_person()

        if person is None:
            return

        selection = self.wish_tree.selection()

        if not selection:
            messagebox.showinfo("No Selection","Select a wish first.")
            return

        index = self.wish_tree.index(selection[0])

        wish = person.wishes[index]

        possible = [p.name for p in self.app.appdata.people if p.name != person.name]

        dialog = WishDialog(self, "Edit Wish", possible, wish.person, wish.weight)

        if dialog.result is None:
            return

        new_person, new_weight = dialog.result

        for i, other in enumerate(person.wishes):
            if (i != index and other.person == new_person):
                messagebox.showerror("Duplicate", "This wish already exists.")
                return

        wish.person = new_person
        wish.weight = new_weight

        self.refresh_wishes()

    def remove_selected_wish(self):
        person = self.get_selected_person()

        if person is None:
            return

        selection = self.wish_tree.selection()

        if not selection:
            return

        index = self.wish_tree.index(selection[0])

        del person.wishes[index]

        self.refresh_wishes()



class PersonDialog(DialogBase):
    def __init__(self, parent, title, name="", gender="M"):
        super().__init__(parent, title)

        frame = ttk.Frame(self, padding=15)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Person name:").pack(anchor="w")

        self.name_var = tk.StringVar(value=name)

        entry = ttk.Entry(frame, textvariable=self.name_var, width=40)
        entry.pack(fill="x", pady=(5, 15))

        ttk.Label(frame, text="Gender:").pack(anchor="w")
        self.gender_var = tk.StringVar(value=gender)
        gender_combo = ttk.Combobox( frame, textvariable=self.gender_var, values=("F", "M"), state="readonly", width=10 )
        gender_combo.pack(anchor="w", pady=(5, 15))

        buttons = ttk.Frame(frame)
        buttons.pack(fill="x")

        ttk.Button(buttons, text="Cancel", command=self.cancel).pack(side="right", padx=5)
        ttk.Button(buttons, text="OK", command=self.ok).pack(side="right", padx=5)

        entry.focus_set()

        self.bind("<Return>", lambda e: self.ok())
        self.bind("<Escape>", lambda e: self.cancel())

        self.wait_window()

    def ok(self):
        name = self.name_var.get().strip()

        if not name:
            messagebox.showerror("Invalid", "Person name cannot be empty.", parent=self)
            return

        gender = self.gender_var.get()

        self.result = name, gender
        self.destroy()


class WishDialog(DialogBase):
    def __init__(self, parent, title, people, selected_person=None, weight=1):
        super().__init__(parent, title)

        frame = ttk.Frame(self, padding=15)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Person:").grid(row=0, column=0, sticky="w", pady=5)

        self.person_var = tk.StringVar(value=selected_person or people[0])

        ttk.Combobox(frame, textvariable=self.person_var, values=people, state="readonly", width=35).grid(row=0, column=1, sticky="ew", pady=5)

        ttk.Label(frame, text="Weight:").grid(row=1, column=0, sticky="w", pady=5)

        self.weight_var = tk.StringVar(value=str(weight))

        ttk.Entry(frame, textvariable=self.weight_var, width=10).grid(row=1, column=1, sticky="w", pady=5)

        ttk.Label(frame, text="Higher values mean a stronger preference.").grid(row=2, column=0, columnspan=2, sticky="w", pady=(5, 15))

        buttons = ttk.Frame(frame)
        buttons.grid(row=3, column=0, columnspan=2, sticky="e")

        ttk.Button(buttons, text="Cancel", command=self.cancel).pack(side="right", padx=5)
        ttk.Button(buttons, text="OK", command=self.ok).pack(side="right", padx=5)

        frame.columnconfigure(1, weight=1)

        self.bind("<Return>", lambda e: self.ok())
        self.bind("<Escape>", lambda e: self.cancel())

        self.wait_window()

    def ok(self):
        person = self.person_var.get()

        try:
            weight = int(self.weight_var.get())
        except ValueError:
            messagebox.showerror("Invalid", "Weight must be an integer.", parent=self)
            return

        self.result = (person, weight)

        self.destroy()
