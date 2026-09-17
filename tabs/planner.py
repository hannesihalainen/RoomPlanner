import queue
import threading
import tkinter as tk
from tkinter import ttk, messagebox

import rplanner
import planners.hitpbo
#import planners.greedy
from rpmodels import *

class PlannerTab(ttk.Frame):
    def __init__(self, app, tab):
        super().__init__(app.notebook)
        self.app = app
        self.tab = tab

        # Planner thread state.
        self.planner_thread = None
        self.planner_stop_event = None
        self.planner_queue = queue.Queue()

        # Poll background planner messages.
        self.after(100, self.process_planner_queue)

    def create(self):
        container = ttk.Frame(self.tab, padding=10)
        container.pack(fill="both", expand=True)

        ttk.Label(container, text="Room Planning", font=("TkDefaultFont", 16, "bold")).pack(anchor="w", pady=(0, 10))

        # Solver controls
        controls = ttk.LabelFrame(container, text="Planner")
        controls.pack(fill="x", pady=(0, 10))

        ttk.Label(controls, text="Solver:").grid(row=0, column=0, padx=10, pady=10)

        self.solver_var = tk.StringVar()

        self.solver_combo = ttk.Combobox(controls, textvariable=self.solver_var, state="readonly", width=35)

        self.solver_combo.grid(row=0, column=1, padx=5, pady=10)

        ttk.Button(controls, text="Plan", command=self.start_planning).grid(row=0, column=2, padx=10, pady=10)

        self.stop_button = ttk.Button(controls, text="Stop", command=self.stop_planning, state="disabled")

        self.stop_button.grid(row=0, column=3, padx=5, pady=10)

        ttk.Button(controls, text="Export Plan...", command=self.app.export_plan).grid(row=0, column=4, padx=10, pady=10)

        # Status
        status_frame = ttk.Frame(container)
        status_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(status_frame, text="Status:").pack(side="left")

        self.status_var = tk.StringVar(value="Idle")

        ttk.Label(status_frame, textvariable=self.status_var).pack(side="left", padx=8)

        self.progress = ttk.Progressbar(status_frame, mode="indeterminate")

        self.progress.pack(side="right", fill="x", expand=True, padx=(20, 0))

        # Plan view
        plan_frame = ttk.LabelFrame(container, text="Current Plan")
        plan_frame.pack(fill="both", expand=True)

        plan_tree_frame = ttk.Frame(plan_frame, padding=5)
        plan_tree_frame.pack(fill="both", expand=True)

        self.plan_tree = ttk.Treeview(plan_tree_frame, columns=("capacity",), show="tree headings")

        self.plan_tree.heading("#0", text="Room / People")

        self.plan_tree.heading("capacity", text="Capacity")

        self.plan_tree.column("#0", width=500)

        self.plan_tree.column("capacity", width=150, anchor="center")

        scrollbar = ttk.Scrollbar(plan_tree_frame, orient="vertical", command=self.plan_tree.yview)

        self.plan_tree.configure(yscrollcommand=scrollbar.set)

        self.plan_tree.pack(side="left", fill="both", expand=True)

        scrollbar.pack(side="right", fill="y")

        # Plan evaluation view
        evaluation_frame = ttk.LabelFrame(container, text="Plan Evaluation")
        evaluation_frame.pack(fill="x", pady=(10, 0))

        self.evaluation_var = tk.StringVar(value="No plan to evaluate.")

        ttk.Label(evaluation_frame, textvariable=self.evaluation_var).pack(anchor="w", padx=10, pady=10)

        columns_frame = ttk.Frame(evaluation_frame)
        columns_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        satisfied_frame = ttk.LabelFrame(columns_frame, text="Satisfied Wishes")
        satisfied_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        unsatisfied_frame = ttk.LabelFrame(columns_frame, text="Unsatisfied Wishes")
        unsatisfied_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        self.satisfied_tree = ttk.Treeview(satisfied_frame, columns=("person", "wish", "weight"), show="headings", height=5)

        self.satisfied_tree.heading("person", text="Person")
        self.satisfied_tree.heading("wish", text="Wish")
        self.satisfied_tree.heading("weight", text="Weight")

        self.satisfied_tree.column("person", width=90)
        self.satisfied_tree.column("wish", width=120)
        self.satisfied_tree.column("weight", width=40, anchor="center")

        self.satisfied_tree.pack(fill="x", expand=True, padx=5, pady=5)


        self.unsatisfied_tree = ttk.Treeview(unsatisfied_frame, columns=("person", "wish", "weight"), show="headings", height=5)

        self.unsatisfied_tree.heading("person", text="Person")
        self.unsatisfied_tree.heading("wish", text="Wish")
        self.unsatisfied_tree.heading("weight", text="Weight")

        self.unsatisfied_tree.column("person", width=90)
        self.unsatisfied_tree.column("wish", width=120)
        self.unsatisfied_tree.column("weight", width=40, anchor="center")

        self.unsatisfied_tree.pack(fill="x", expand=True, padx=5, pady=5)

        columns_frame.columnconfigure(0, weight=1)
        columns_frame.columnconfigure(1, weight=1)

        self.refresh_solver_list()



    def refresh_solver_list(self):
        names = rplanner.get_planner_names()

        self.solver_combo["values"] = names

        if names:
            if (self.solver_var.get() not in names):
                self.solver_var.set(names[0])
        else:
            self.solver_var.set("")

    def display_plan(self, plan):
        self.app.appdata.current_plan = plan.copy()

        for item in self.plan_tree.get_children():
            self.plan_tree.delete(item)

        room_lookup = {room.name: room for room in self.app.appdata.rooms}

        for room_name, people in plan.assignments.items():
            room = room_lookup.get(room_name)

            if room is None:
                continue

            room_item = self.plan_tree.insert("", "end", text=room_name, values=(f"{len(people)} / {room.size}",), open=True)

            for person in people:
                self.plan_tree.insert(room_item, "end", text=person, values=("",) )
        self.evaluate_plan(plan)


    def evaluate_plan(self, plan):
        if plan is None:
            self.evaluation_var.set("No plan to evaluate.")

            for item in self.unsatisfied_tree.get_children():
                self.unsatisfied_tree.delete(item)

            return

        assignments = {}

        for room_name, people in plan.assignments.items():
            for person in people:
                assignments[person] = room_name

        total_wishes = 0
        satisfied_wishes = 0
        total_weight = 0
        satisfied_weight = 0
        satisfied = []
        unsatisfied = []

        for person in self.app.appdata.people:
            person_room = assignments.get(person.name)

            for wish in person.wishes:
                total_wishes += 1
                total_weight += wish.weight

                wish_room = assignments.get(wish.person)

                if person_room is not None and person_room == wish_room:
                    satisfied_wishes += 1
                    satisfied_weight += wish.weight
                    satisfied.append((person.name, wish.person, wish.weight))
                else:
                    unsatisfied.append((person.name, wish.person, wish.weight))

        if total_weight > 0:
            percentage = 100 * satisfied_weight / total_weight
        else:
            percentage = 100.0

        self.evaluation_var.set(
            f"Satisfied wishes: {satisfied_wishes} / {total_wishes}    "
            f"Score: {satisfied_weight} / {total_weight}    "
            f"({percentage:.1f}%)"
        )

        for item in self.unsatisfied_tree.get_children():
            self.unsatisfied_tree.delete(item)

        for person, wish, weight in unsatisfied:
            self.unsatisfied_tree.insert("", "end", values=(person, wish, weight))

        for item in self.satisfied_tree.get_children():
            self.satisfied_tree.delete(item)

        for person, wish, weight in satisfied:
            self.satisfied_tree.insert("", "end", values=(person, wish, weight))

    # ============================================================
    # ASYNC PLANNING
    # ============================================================

    def start_planning(self):
        if (self.planner_thread and self.planner_thread.is_alive()):
            return

        solver_name = self.solver_var.get()

        if not solver_name:
            messagebox.showerror("No Planner", "No planner solver is available.")
            return



        # Snapshot the input. This means the user can edit the GUI
        # while a planner is running without modifying its input.
        context = rplanner.PlannerContext(
            rooms=[Room(r.name, r.size) for r in self.app.appdata.rooms],
            people=[Person(p.name, p.gender, [Wish(w.person, w.weight) for w in p.wishes]) for p in self.app.appdata.people],
            constraints=[Constraint(type=c.type, person1=c.person1, person2=c.person2, person=c.person, room=c.room, room1=c.room1, room2=c.room2) for c in self.app.appdata.constraints]
        )

        self.app.appdata.current_plan = None
        self.clear_plan_view()
        self.status_var.set(f"Running: {solver_name}")
        self.progress.start(10)
        self.stop_button.config(state="normal")
        self.planner_stop_event = (threading.Event())
        stop_event = self.planner_stop_event
        self.planner_thread = threading.Thread(target=self.run_planner_thread, args=(solver_name, context, stop_event), daemon=True)
        self.planner_thread.start()

    def run_planner_thread(self, solver_name, context, stop_event):
        try:
            planner = rplanner.create_planner(solver_name)

            def send_solution(plan):
                self.planner_queue.put(("solution", plan.copy()))

            def is_cancelled():
                return stop_event.is_set()

            def send_status(text):
                self.planner_queue.put(("status", text))

            callbacks = rplanner.PlannerCallbacks(
                send_solution=send_solution,
                is_cancelled=is_cancelled,
                send_status=send_status
            )

            result = planner.solve(context, callbacks)
            self.planner_queue.put(("finished", result))
        except Exception as e:
            self.planner_queue.put(("error", e))

    def stop_planning(self):
        if (self.planner_thread and self.planner_thread.is_alive() and self.planner_stop_event):
            self.planner_stop_event.set()
            self.status_var.set("Stopping...")
            self.stop_button.config(state="disabled")

    def process_planner_queue(self):
        try:
            while True:
                message_type, payload = (self.planner_queue.get_nowait())
                if message_type == "solution":
                    self.display_plan(payload)
                elif message_type == "status":
                    self.status_var.set(payload)
                elif message_type == "finished":
                    self.planner_finished(payload)
                elif message_type == "error":
                    self.planner_error(payload)
        except queue.Empty:
            pass
        self.after(100, self.process_planner_queue)

    def planner_finished(self, result: PlannerResult):
        self.progress.stop()
        self.stop_button.config(state="disabled")
        if result.plan is not None:
            self.display_plan(result.plan)
        if result.possible:
            self.status_var.set("Finished")
        else:
            if (self.planner_stop_event and self.planner_stop_event.is_set()):
                self.status_var.set("Stopped")
            else:
                self.status_var.set("Not possible")
                self.clear_plan_view()
                messagebox.showinfo("Not Possible", result.message or "No valid plan could be found.")

    def planner_error(self, error):
        self.progress.stop()
        self.stop_button.config(state="disabled")
        self.status_var.set("Error")
        messagebox.showerror("Planner Error", str(error))


    def clear_plan_view(self):
        self.app.appdata.current_plan = None
        for item in self.plan_tree.get_children():
            self.plan_tree.delete(item)
