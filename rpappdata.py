import json

from rpmodels import *

class RPAppData:
    def __init__(self):
        self.rooms = []
        self.people = []
        self.constraints = []
        self.current_plan = None


    # ============================================================
    # ROOM FILES
    # ============================================================

    def save_rooms(self, filename):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump({"rooms": self.rooms_to_json()}, f, indent=4, ensure_ascii=False)

    def load_rooms(self, filename):
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.load_rooms_from_data(data)

    def load_rooms_from_data(self, data):
        new_rooms = []

        for r in data["rooms"]:
            new_rooms.append(Room(r["name"], int(r["size"])))

        names = [r.name for r in new_rooms]

        if len(names) != len(set(names)):
            raise ValueError("The file contains duplicate room names.")

        self.rooms = new_rooms

        room_names = set(names)

        # Remove now-invalid room constraints.
        self.constraints = [c for c in self.constraints if (c.type not in ("to_room", "not_to_room") or c.room in room_names)]


    # ============================================================
    # PEOPLE FILES
    # ============================================================

    def save_people(self, filename):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump({"people": self.people_to_json()}, f, indent=4, ensure_ascii=False)


    def load_people(self, filename):
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.load_people_from_data(data)


    def load_people_from_data(self, data):
        new_people = []

        for p in data["people"]:
            wishes = [Wish(w["person"],int(w["weight"])) for w in p.get("wishes", [])]
            new_people.append(Person(p["name"], p.get("gender", "M"), wishes))

        names = [p.name for p in new_people]

        if len(names) != len(set(names)):
            raise ValueError("The file contains duplicate people.")

        person_names = set(names)

        for person in new_people:
            for wish in person.wishes:
                if wish.person not in person_names:
                    raise ValueError(f"Wish of {person.name} refers to " f"unknown person {wish.person}.")

        self.people = new_people

        self.constraints = [c for c in self.constraints if self.constraint_people_exist(c, person_names)]

    def import_people(self, filename, gendered = True):
        names = set([p.name for p in self.people])
        with open(filename, "r", encoding="utf-8") as f:
            for l in f:
                gender = "M"
                if gendered:
                    gender = l[0]
                    l=l[1:]
                name = l.strip()
                if name in names: continue
                self.people.append(Person(name, gender, []))
                names.add(name)


    def constraint_people_exist(self, c, person_names):
        if c.type in ("same", "different"):
            return c.person1 in person_names and c.person2 in person_names
        elif c.type in ("to_room", "not_to_room"):
            return c.person in person_names
        return True

    # ============================================================
    # CONSTRAINT FILES
    # ============================================================

    def save_constraints(self, filename):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump({"constraints": self.constraints_to_json()}, f, indent=4, ensure_ascii=False)

    def load_constraints(self, filename):
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.load_constraints_from_data(data)

    def load_constraints_from_data(self, data):
        person_names = {p.name for p in self.people}

        room_names = {r.name for r in self.rooms}

        new_constraints = []

        for c in data["constraints"]:
            ctype = c["type"]

            if ctype in ("same", "different"):
                if (c["person1"] not in person_names or c["person2"] not in person_names):
                    raise ValueError("Constraint references an unknown person.")
                new_constraints.append(Constraint(type=ctype, person1=c["person1"], person2=c["person2"]))
            elif ctype in ("to_room", "not_to_room"):
                if c["person"] not in person_names:
                    raise ValueError("Constraint references an unknown person.")
                if c["room"] not in room_names:
                    raise ValueError("Constraint references an unknown room.")
                new_constraints.append(Constraint(type=ctype, person=c["person"], room=c["room"]))
            elif ctype in ("male", "female"):
                if c["room"] not in room_names:
                    raise ValueError("Constraint references an unknown room.")
                new_constraints.append(Constraint(type=ctype, room=c["room"]))
            elif ctype in ("same_gender"):
                if c["room1"] not in room_names or c["room2"] not in room_names:
                    raise ValueError("Constraint references an unknown room.")
                new_constraints.append(Constraint(type=ctype, room1=c["room1"], room2=c["room2"]))

            else:
                raise ValueError(f"Unknown constraint type: {ctype}")

        self.constraints = new_constraints





    # ============================================================
    # COMPLETE PROJECT
    # ============================================================

    def save_project(self, filename):
        data = {
            "version": 2,
            "rooms": self.rooms_to_json(),
            "people": self.people_to_json(),
            "constraints": self.constraints_to_json()
        }

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)


    def load_project(self, filename):
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.load_rooms_from_data(data)
        self.load_people_from_data(data)
        self.load_constraints_from_data(data)

    # ============================================================
    # EXPORT PLANS
    # ============================================================

    def export_plan(self, filename):
        if filename.endswith(".json"): self.export_plan_json(filename)
        else: export_plan_text(filename)

    def export_plan_json(self, filename):
        data = {"assignments": self.current_plan.assignments}
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def export_plan_text(self, filename):
        room_lookup = {room.name: room for room in self.rooms}
        with open(filename, "w", encoding="utf-8") as f:
            for room_name, people in (self.current_plan.assignments.items()):
                room = room_lookup.get(room_name)
                if room:
                    f.write(f"{room_name} " f"({len(people)}/{room.size})\n")
                else:
                    f.write(f"{room_name}\n")
                for person in people:
                    f.write(f"  - {person}\n")
                f.write("\n")


    # ============================================================
    # JSON HELPERS
    # ============================================================

    def rooms_to_json(self):
        return [{"name": room.name, "size": room.size} for room in self.rooms]

    def people_to_json(self):
        return [
            {"name": person.name, "gender": person.gender, "wishes": [{"person": wish.person, "weight": wish.weight} for wish in person.wishes]}
            for person in self.people
        ]

    def constraints_to_json(self):
        result = []
        for c in self.constraints:
            data = {"type": c.type}
            if c.type in ("same", "different"):
                data["person1"] = c.person1
                data["person2"] = c.person2
            elif c.type in ("to_room", "from_room"):
                data["person"] = c.person
                data["room"] = c.room
            elif c.type in ("male", "female"):
                data["room"] = c.room
            elif c.type in ("same_gender"):
                data["room1"] = c.room1
                data["room2"] = c.room2
            result.append(data)
        return result
