

class MySolver(Planner):
    name = "My External Solver"

    def solve(self, context, callbacks):
        # context.rooms
        # context.people
        # context.constraints

        # Example:
        #
        # assignments = {
        #     room.name: []
        #     for room in context.rooms
        # }

        # Do expensive solver work here.

        # Whenever an intermediate solution is found:
        #
        # callbacks.send_solution(
        #     RoomPlan(assignments)
        # )

        # Report progress:
        #
        # callbacks.status("Solving iteration 42...")

        # Allow the UI to stop the solver:
        #
        # if callbacks.is_cancelled():
        #     return PlannerResult(
        #         possible=False,
        #         message="Stopped by user."
        #     )

        # Return the final result:
        #
        # return PlannerResult(
        #     possible=True,
        #     plan=RoomPlan(assignments),
        #     message="Done"
        # )

        raise NotImplementedError


register_planner(MySolver)


### Adding a real solver
"""
The important part is that a solver does **not** need to know anything about Tkinter.

For example, you could put this into `my_solver.py`:

```python
from room_planner import (
    Planner,
    PlannerResult,
    RoomPlan,
    register_planner,
)

```

Then, before starting the application, import that module:

```python
import my_solver
```

and `"My External Solver"` will automatically appear in the **Algorithm** dropdown.

### Solver API

The interface between the GUI and solver is intentionally small:

```text
PlannerContext
    ├── rooms
    ├── people
    │     └── wishes
    └── constraints

PlannerCallbacks
    ├── send_solution(plan)
    ├── status(message)
    └── is_cancelled()

PlannerResult
    ├── possible
    ├── plan
    └── message
```

A long-running solver can therefore do:

```python
for iteration in range(1000000):

    if callbacks.is_cancelled():
        return PlannerResult(
            possible=False,
            message="Stopped."
        )

    # solver work...

    if found_interesting_solution:
        callbacks.send_solution(
            RoomPlan(assignments)
        )

    callbacks.status(
        f"Iteration {iteration}"
    )
```

The callback calls happen on the solver's background thread; the GUI automatically transfers them to the Tkinter main thread through a `queue.Queue`, so solver code doesn't need to interact with Tkinter directly.

One further change I would make once you start adding actual solvers is to move the **data model + planner API into `planner_api.py`**, the GUI into `room_planner.py`, and each backend into its own module/package. That will let you add OR-Tools, CP-SAT, ILP, custom search, or an external executable without making the GUI increasingly large.
"""
