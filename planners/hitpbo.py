import hitpbo

from rplanner import Planner, register_planner
from rpmodels import *


def cardinality_constraint(lits, tp, rhs):
    lhs = [[1, l] for l in lits]
    if tp=="<":
        for t in lhs: t[0]=-1
        rhs = -rhs
        rhs+=1
    elif tp=="<=":
        for t in lhs: t[0]=-1
        rhs = -rhs
    elif tp==">":
        for t in lhs: t[0]=-1
        rhs+=1
    elif tp==">=":
        pass
    else:
        raise ValueError(f"Invalid type {tp}")
    return [lhs, rhs]


def var_p2r(pi, ri, context):
    return pi*len(context.rooms) + ri + 1
    
    
def pr_from_var(var, context):
    return (var-1)//len(context.rooms), (var-1)%(len(context.rooms))

def var_g(ri, context):
    return len(context.rooms)*len(context.people) + ri + 1
    
def var_sr(p1, p2, context):
    if p2<p1: return var_sr(p2, p1, context)
    return len(context.rooms)*len(context.people) + p1*len(context.people) + len(context.rooms) + p2 + 1

class HitPBO(Planner):
    name = "HitPBO"
    
    def solve(self, context, callbacks):
        solver = hitpbo.HitPBO()

        # set configuration for the solver
        #solver.set_int_option("verbose", 3)
        #solver.set_bool_option("presolve", False)
        #solver.set_bool_option("proof-compatible", True)

        # Initialize solver
        solver.initialize()
        
        p2i = {}
        r2i = {}
        for pi, p in enumerate(context.people):
            p2i[p.name]=pi
        for ri, r in enumerate(context.rooms):
            r2i[r.name]=ri
        
        # each person to at least one room
        for pi, p in enumerate(context.people):
            l = []
            for ri, r in enumerate(context.rooms):
                l.append(var_p2r(pi, ri, context))
            constraint = cardinality_constraint(l, ">=", 1)
            solver.add_constraint(constraint[0], constraint[1])
            constraint = cardinality_constraint(l, "<=", 1)
            solver.add_constraint(constraint[0], constraint[1])
            
        # if person goes to a room, that room's gender must correspond to the persons gender
        for pi, p in enumerate(context.people):
            for ri, r in enumerate(context.rooms):
                v = var_p2r(pi, ri, context)
                vg = var_g(ri, context)
                if p.gender=="M":
                    solver.add_constraint([[1, -v], [1, vg]], 1)
                else:
                    solver.add_constraint([[1, -v], [1, -vg]], 1)
                    
                   
        # maximum size for each room
        for ri, r in enumerate(context.rooms):
            l = []
            for pi, p in enumerate(context.people):
                l.append(var_p2r(pi, ri, context))
            constraint = cardinality_constraint(l, "<=", r.size)
            solver.add_constraint(constraint[0], constraint[1])
        
        # for each pair of persons, variable to indicate if they are in the same room
        for p1 in range(len(context.people)):
            for p2 in range(p1+1, len(context.people)):
                vsr = var_sr(p1, p2, context)
                for ri, r in enumerate(context.rooms):
                    v1 = var_p2r(p1, ri, context)
                    v2 = var_p2r(p2, ri, context)
                    solver.add_constraint([[1, v1], [1, -v2], [1, -vsr]], 1)
                    solver.add_constraint([[1, -v1], [1, v2], [1, -vsr]], 1)
                    solver.add_constraint([[1, -v1], [1, -v2], [1, vsr]], 1)
                        
        # special constraints
        for c in context.constraints:
            if c.type=="same":
                p1=p2i[c.person1]
                p2=p2i[c.person2]
                vsr = var_sr(p1, p2, context)
                solver.add_constraint([[1, vsr]], 1)
            elif c.type=="different":
                p1=p2i[c.person1]
                p2=p2i[c.person2]
                vsr = var_sr(p1, p2, context)
                solver.add_constraint([[1, -vsr]], 1)
            elif c.type=="to_room":
                pi=p2i[c.person]
                ri=r2i[c.room]
                v = var_p2r(pi, ri, context)
                solver.add_constraint([[1, v]], 1)
            elif c.type=="not_to_room":
                pi=p2i[c.person]
                ri=r2i[c.room]
                v = var_p2r(pi, ri, context)
                solver.add_constraint([[1, -v]], 1)
            elif c.type=="male":
                ri=r2i[c.room]
                vg = var_g(ri, context)
                solver.add_constraint([[1, vg]], 1)
            elif c.type=="female":
                ri=r2i[c.room]
                vg = var_g(ri, context)
                solver.add_constraint([[1, -vg]], 1)
            elif c.type=="same_gender":
                r1=r2i[c.room1]
                r2=r2i[c.room2]
                vg1 = var_g(r1, context)
                vg2 = var_g(r2, context)
                print(vg1, vg2)
                solver.add_constraint([[1, -vg1], [1, vg2]], 1)
                solver.add_constraint([[1, vg1], [1, -vg2]], 1)
            else:
                print("UNKNOWN TYPE", c.type)
                
        objective=[]
        for p1, p in enumerate(context.people):
            for w in p.wishes:
                p2 = p2i[w.person]
                w = w.weight
                vsr = var_sr(p1, p2, context)
                objective.append([-w, vsr])
                
        solver.set_objective(objective)
        r = result = solver.solve()
        if r==hitpbo.Result.UNSAT:
            return PlannerResult(possible=False, plan=None, message="Not possible to make a plan")
        elif r==hitpbo.Result.UNSUPPORTED:
            return PlannerResult(possible=False, plan=None, message="HitPBO returned UNSUPPORTED")
        elif r==hitpbo.Result.UNKNOWN:
            return PlannerResult(possible=False, plan=None, message="UNKNOWN")
        elif r==hitpbo.Result.SAT or r==hitpbo.Result.OPTIMAL:
        
            assignments = {
                 room.name: []
                 for room in context.rooms
            }
            solution = solver.get_solution()
            for lit in solution:
                if abs(lit)>len(context.rooms)*len(context.people): break
                if lit>0:
                    pi, ri = pr_from_var(lit, context)
                    assignments[context.rooms[ri].name].append(context.people[pi].name)
            
            #print("Solution literals:", solution)
            if r==hitpbo.Result.SAT:
                return PlannerResult(possible=True, plan=RoomPlan(assignments), message="Plan but not necessarily optimal")
            else:
                return PlannerResult(possible=True, plan=RoomPlan(assignments), message="Plan but not necessarily optimal")
        else:
            print("WHAT")
            print(r)
            return PlannerResult(possible=False, plan=None, message="WHAT")
        return PlannerResult(possible=False, plan=None, message="WHAT2")
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


register_planner(HitPBO)


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
