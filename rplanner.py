from rpmodels import *
from typing import Callable


class PlannerCallbacks:
    """
    Callbacks available to planner implementations.

    The important property is that a planner never has to know
    anything about Tkinter.

    send_solution() can be called whenever the planner finds a
    better/intermediate solution.

    is_cancelled() should be checked regularly by long-running
    planners.
    """

    def __init__(
        self,
        send_solution: Callable[[RoomPlan], None],
        is_cancelled: Callable[[], bool],
        send_status: Callable[[str], None],
    ):
        self._send_solution = send_solution
        self._is_cancelled = is_cancelled
        self._send_status = send_status

    def send_solution(self, plan: RoomPlan):
        self._send_solution(plan)

    def is_cancelled(self):
        return self._is_cancelled()

    def status(self, text: str):
        self._send_status(text)


class Planner:
    """
    Base class for planner algorithms.

    To implement a new solver:

        class MySolver(Planner):
            name = "My Solver"

            def solve(self, context, callbacks):
                ...
                return PlannerResult(...)

    Then register it:

        register_planner(MySolver)
    """

    name = "Unnamed Planner"

    def solve(
        self,
        context: PlannerContext,
        callbacks: PlannerCallbacks
    ) -> PlannerResult:
        raise NotImplementedError


# ================================================================
# PLANNER REGISTRY
# ================================================================

PLANNER_REGISTRY = {}


def register_planner(planner_class):
    """
    Register a planner class.

    Example:

        register_planner(MySolver)
    """

    name = planner_class.name

    if not name:
        raise ValueError(
            "Planner must define a non-empty 'name'."
        )

    PLANNER_REGISTRY[name] = planner_class


def get_planner_names():
    return sorted(PLANNER_REGISTRY.keys())


def create_planner(name):
    planner_class = PLANNER_REGISTRY.get(name)

    if planner_class is None:
        raise ValueError(
            f"Unknown planner: {name}"
        )

    return planner_class()
    
    

