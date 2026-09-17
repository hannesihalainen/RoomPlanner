from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


@dataclass
class Room:
    name: str
    size: int


@dataclass
class Wish:
    person: str
    weight: int


@dataclass
class Person:
    name: str
    gender: str
    wishes: List[Wish] = field(default_factory=list)


@dataclass
class Constraint:
    type: str

    # Used by same/different
    person1: Optional[str] = None
    person2: Optional[str] = None

    # Used by to_room/not_to_room, room used by male/female
    person: Optional[str] = None
    room: Optional[str] = None

    # Used by same_gender
    room1: Optional[str] = None
    room2: Optional[str] = None


@dataclass
class RoomPlan:
    """
    A snapshot of a room assignment.

    assignments maps room name -> list of people.
    """
    assignments: Dict[str, List[str]]

    def copy(self):
        return RoomPlan(assignments={ room: list(people) for room, people in self.assignments.items()})


@dataclass
class PlannerResult:
    """
    Final result returned by a planner.
    """

    possible: bool
    plan: Optional[RoomPlan] = None
    message: str = ""


@dataclass
class PlannerContext:
    """
    Immutable-ish input supplied to a planner.

    A planner should not modify these objects.
    """

    rooms: List[Room]
    people: List[Person]
    constraints: List[Constraint]

    def room_by_name(self, name):
        for room in self.rooms:
            if room.name == name:
                return room
        return None

    def person_by_name(self, name):
        for person in self.people:
            if person.name == name:
                return person
        return None
