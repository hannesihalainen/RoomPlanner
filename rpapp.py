import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import rplanner
import rpappdata
from tabs.rooms import RoomTab
from tabs.people import PeopleTab
from tabs.constraints import ConstraintTab
from tabs.planner import PlannerTab

# ================================================================
# MAIN TKINTER APPLICATION
# ================================================================

class RoomPlannerApp(tk.Tk):

    def __init__(self):
        super().__init__()

        self.title("Room Planner")
        self.geometry("1100x750")
        self.minsize(900, 600)

        self.appdata = rpappdata.RPAppData()


        # Last available plan.

        self.create_menu()
        self.create_ui()


    # ============================================================
    # MENU
    # ============================================================


    def create_menu(self):
        menubar = tk.Menu(self)

        file_menu = tk.Menu(menubar, tearoff=False)

        file_menu.add_command(label="Save Rooms...", command=self.save_rooms)
        file_menu.add_command(label="Load Rooms...", command=self.load_rooms)

        file_menu.add_separator()

        file_menu.add_command(label="Save People...", command=self.save_people)
        file_menu.add_command(label="Load People...", command=self.load_people)

        file_menu.add_separator()

        file_menu.add_command(label="Save Constraints...", command=self.save_constraints)
        file_menu.add_command(label="Load Constraints...", command=self.load_constraints)

        file_menu.add_separator()

        file_menu.add_command(label="Save Complete Project...", command=self.save_project)
        file_menu.add_command(label="Load Complete Project...", command=self.load_project)

        file_menu.add_separator()

        file_menu.add_command(label="Exit", command=self.destroy)

        menubar.add_cascade(label="File", menu=file_menu)

        self.config(menu=menubar)


    # ============================================================
    # MAIN UI
    # ============================================================
    def create_ui(self):
        notebook = ttk.Notebook(self)
        self.notebook = notebook
        notebook.pack(fill="both", expand=True, padx=8, pady=8)

        self.rooms_tab = RoomTab(self, ttk.Frame(notebook))
        self.people_tab = PeopleTab(self, ttk.Frame(notebook))
        self.constraints_tab = ConstraintTab(self, ttk.Frame(notebook))
        self.planner_tab = PlannerTab(self, ttk.Frame(notebook))

        notebook.add(self.rooms_tab.tab, text="Rooms")
        notebook.add(self.people_tab.tab, text="People & Wishes")
        notebook.add(self.constraints_tab.tab, text="Constraints")
        notebook.add(self.planner_tab.tab, text="Planning")

        self.rooms_tab.create()
        self.people_tab.create()
        self.constraints_tab.create()
        self.planner_tab.create()

    def refresh_rooms(self):
        self.rooms_tab.refresh_rooms()

    def refresh_people(self):
        self.people_tab.refresh_people()

    def refresh_constraints(self):
        self.constraints_tab.refresh_constraints()

    # ============================================================
    # SAVE AND LOAD FILES
    # ============================================================

    # helper functions to create dialogs
    def save_filename(self, title):
        return  filedialog.asksaveasfilename(title=title, defaultextension=".json", filetypes=[("JSON files", "*.json"), ("All files", "*.*")])

    def load_filename(self, title):
        return  filedialog.askopenfilename(title=title, defaultextension=".json", filetypes=[("JSON files", "*.json"), ("All files", "*.*")])


    # Saving and loading rooms
    def save_rooms(self):
        filename = self.save_filename("Save Rooms")
        if not filename: return
        try:
            self.appdata.save_rooms(filename)
        except Exception as e:
            messagebox.showerror("Save Error", str(e))

    def load_rooms(self):
        filename = self.load_filename("Load Rooms")
        if not filename: return
        try:
            self.appdata.load_rooms(filename)
            self.refresh_rooms()
            self.refresh_constraints()
        except Exception as e:
            messagebox.showerror("Load Error", str(e))

    # Saving and loading people

    def save_people(self):
        filename = self.save_filename("Save People")
        if not filename: return
        try:
            self.appdata.save_people(filename)
        except Exception as e:
            messagebox.showerror("Save Error", str(e))

    def load_people(self):
        filename = self.load_filename("Load People")
        if not filename: return
        try:
            self.appdata.load_people(filename)
            self.refresh_people()
            self.refresh_constraints()
        except Exception as e:
            messagebox.showerror("Load Error", str(e))

    # Saving and loading constraints

    def save_constraints(self):
        filename = self.save_filename("Save Constraints")
        if not filename: return
        try:
            self.appdata.save_constraints(filename)
        except Exception as e:
            messagebox.showerror("Save Error", str(e))

    def load_constraints(self):
        filename = self.load_filename("Load Constraints")
        if not filename: return
        try:
            self.appdata.load_constraints(filename)
            self.refresh_constraints()
        except Exception as e:
            messagebox.showerror("Save Error", str(e))


    # Savng and loading the full project

    def save_project(self):
        filename = self.save_filename("Save Complete Project")
        if not filename: return
        try:
            self.appdata.save_project(filename)
        except Exception as e:
            messagebox.showerror("Save Error", str(e))

    def load_project(self):
        filename = self.load_filename("Load Complete Project")
        if not filename: return
        try:
            self.appdata.load_project(filename)
            self.refresh_rooms()
            self.refresh_people()
            self.refresh_constraints()
        except Exception as e:
            messagebox.showerror("Load Error", str(e))

    # Exporting the plan

    def export_plan(self):
        if self.appdata.current_plan is None:
            messagebox.showinfo("No Plan", "There is no plan to export.")
            return

        filename = filedialog.asksaveasfilename(
            title="Export Plan",
            defaultextension=".json",
            filetypes=[
                ("JSON files", "*.json"),
                ("Text files", "*.txt"),
                ("All files", "*.*")
            ]
        )

        if not filename: return
        try:
            self.appdata.export_plan(filename)
            messagebox.showinfo("Exported", "Plan exported successfully.")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))
