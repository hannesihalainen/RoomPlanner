# RoomPlanner

*RoomPlanner* is a simple Python application that assigns people into rooms optimally. Given
- a set of rooms, each with a maximum capacity
- a set of people, each with a gender (M/F)
- a (weighted) wish list for each person, specifying whom they would like to share a room with
- a set of additional constraints

*RoomPlanner* finds a solution that assigns every person to a room, respecting rooms capacities and satisfying all additional constraints.
It also ensures, that all people assigned in the same room will have the same gender.
Among all solutions, *RoomPlanner* finds a solution where the maximum number (/total weight) of wishes is satisfied.

The additional constraints can
- enforce two persons to be assigned to the same room
- enforce two persons to be assigned to different rooms
- enforce a person to be assigned to a specific room
- prevent a person from being assigned to a specific room
- enforce a specific room to be assigned to males/females
- enforce two rooms to be assigned to the same gender

Requirements:
- Python
- HitPBO, install from https://bitbucket.org/coreo-group/hitpbo

