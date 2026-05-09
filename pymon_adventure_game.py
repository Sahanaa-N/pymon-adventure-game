# Pymon Adventure Game
# Object-Oriented Python Adventure Game
# ------------------------------------------------------------
# Known Issues:
# - Random map connections may occasionally isolate some locations.
# - Race animations use time.sleep(), which can slow tests.
# ------------------------------------------------------------
# # References:
# - Python official documentation
# - Python 3.12 documentation
# ------------------------------------------------------------

import csv, os, sys, random, time

# Custom Exceptions
class InvalidDirectionException(Exception):
    pass

class InvalidInputFileFormat(Exception):
    pass

def luck_factor_percent():
    return random.randint(-50, 50)

# Class: Creature
# Base class for all living entities in the game.
# Holds identity, description, speed and adoptability attributes.
class Creature:
    def __init__(self, nickname, description, location=None,
                 adoptable=False, base_speed=5):
        self.nickname = nickname
        self.description = description
        self.location = location
        self.adoptable = adoptable
        self.base_speed = base_speed

    def set_location(self, loc):
        self.location = loc

# Class: Item
# Represents any object that can exist in a Location.
# Items may be pickable/consumable and affect Pymon's stats.
class Item:
    def __init__(self, name, kind, description, pickable=True, consumable=False):
        self.name = name
        self.kind = kind
        self.description = description
        self.pickable = pickable
        self.consumable = consumable

    def __str__(self):
        tag = "" if self.pickable else " [fixed]"
        return f"{self.name}{tag}"

# Class: Location
# Models a physical place with possible door connections.
# Each location maintains lists of creatures and items it contains.
class Location:
    def __init__(self, name, desc, w=None, n=None, e=None, s=None):
        self.name, self.description = name, desc
        self.doors = {"west": w, "north": n, "east": e, "south": s}
        self.creatures, self.items = [], []

    def add_creature(self, c):
        if c not in self.creatures:
            self.creatures.append(c)
            c.set_location(self)

    def remove_creature(self, c):
        if c in self.creatures:
            self.creatures.remove(c)

    def add_item(self, i):
        if i not in self.items:
            self.items.append(i)

    def remove_item(self, i):
        if i in self.items:
            self.items.remove(i)

    def describe(self):
        print(f"\nYou are at {self.name.lower()}, {self.description}")
        if self.items:
            print("Items here:")
            for i in self.items:
                print(f"  - {i}")
        else:
            print("No items here.")
        if self.creatures:
            print("Creatures here:")
            for c in self.creatures:
                print(f"  - {c.nickname}")
        else:
            print("No creatures here.")
        print("Doors:")
        for d, loc in self.doors.items():
            if loc:
                print(f"  {d.title()} → {loc.name}")
        print("")

# Class: Pymon (inherits Creature)
# Player-controlled creature with extra abilities:
# movement, inventory, challenges, and energy management.
class Pymon(Creature):
    def __init__(self, nickname="Toromon",
                 description="White and yellow Pymon with a square face"):
        super().__init__(nickname, description, adoptable=True)
        self.current_location = None
        self.energy = 3
        self.inventory, self.pets = [], []
        self.pogo_active = False
        self.move_count = 0

    def spawn(self, loc):
        self.current_location = loc
        loc.add_creature(self)

    # Inspect 
    def inspect(self):
        while True:
            print("\nInspect Pymon:")
            print("1) Inspect current Pymon")
            print("2) List and select a benched Pymon to use")
            print("3) Back to main menu")
            opt = input("Choose option: ").strip()
            if opt == "1":
                print(f"\nHi Player, my name is {self.nickname}.")
                print(f"My energy level is {self.energy}/3.")
                print(f"I am {self.description}\n")
            elif opt == "2":
                if not self.pets:
                    print("No benched Pymons available.\n")
                    continue
                for i, p in enumerate(self.pets, 1):
                    print(f"{i}) {p.nickname}")
                sel = input("Select number to swap (or Enter to cancel): ").strip()
                if not sel:
                    continue
                try:
                    i = int(sel) - 1
                    new = self.pets[i]
                    self.pets[i] = self
                    print(f"Swapped to {new.nickname}.\n")
                    return new
                except Exception:
                    print("Invalid selection.\n")
            elif opt == "3":
                return self
            else:
                print("Invalid choice.\n")

    # Movement 
    def move(self, d):
        try:
            doors = self.current_location.doors
            if not doors.get(d):
                raise InvalidDirectionException
            nxt = doors[d]
            self.current_location.remove_creature(self)
            nxt.add_creature(self)
            self.current_location = nxt
            print(f"You traveled {d} and arrived at {nxt.name.lower()}.\n")
            self.move_count += 1

            # Energy decreases every 2 moves
            if self.move_count % 2 == 0:
                self.energy -= 1
                print(f"Energy decreased to {self.energy}/3 after travelling.\n")
                if self.energy <= 0:
                    print(f"{self.nickname} has no energy left and escaped into the wild!\n")
                    if not self.pets:
                        print("Game Over — you have no other Pymons!\n")
                        sys.exit(0)
                    new = self.pets.pop(0)
                    new.inventory.extend(self.inventory)
                    print(f"{new.nickname} becomes your new Pymon.\n")
                    return new
        except InvalidDirectionException:
            print(f"There is no door to the {d}. Pymon remains at its current location.\n")
        return self

    # Pick / Use Item 
    def pick_item(self):
        loc = self.current_location
        if not loc.items:
            print("There are no items here.\n")
            return

        print("Available items here:")
        for it in loc.items:
            print(f" - {it.name}")

        name = input("Pick which item: ").strip().lower()
        item = next((i for i in loc.items if i.name.lower() == name), None)

        if not item:
            print(f"No item named '{name}' found here.\n")
            return
        if not item.pickable:
            print(f"The {item.name} cannot be picked up.\n")
            return

        loc.remove_item(item)
        self.inventory.append(item)
        article = "an" if item.name[0].lower() in "aeiou" else "a"
        print(f"You picked up {article} {item.name.lower()} from the ground.\n")

    def show_inventory(self):
        if not self.inventory:
            print("You are carrying nothing.\n")
            return
        inv = ", ".join(i.name.lower() for i in self.inventory)
        print(f"You are carrying: {inv}\n")
        use = input("Use an item? (y/n): ").strip().lower()
        if use == "y":
            self.use_item()

    def use_item(self):
        if not self.inventory:
            print("Your inventory is empty.\n")
            return
        print("Which item would you like to use?")
        for i, it in enumerate(self.inventory, 1):
            print(f"{i}) {it.name} - {it.description}")
        sel = input("Enter number or name: ").strip().lower()
        item = None
        for it in self.inventory:
            if it.name.lower() == sel or sel == str(self.inventory.index(it)+1):
                item = it
                break
        if not item:
            print("Invalid item selection.\n")
            return

        if item.name.lower() == "apple":
            if self.energy < 3:
                self.energy += 1
                print(f"{self.nickname} ate an apple. Energy now {self.energy}/3.\n")
                self.inventory.remove(item)
            else:
                print("Energy already full. Apple not eaten.\n")

        elif item.name.lower() == "pogo stick":
            self.pogo_active = True
            print("Pogo stick activated — next race speed will double!\n")

        elif item.name.lower() == "binocular":
            self.binocular_view()

        else:
            print("This item cannot be used right now.\n")

    def binocular_view(self):
        direction = input("Look where? (current/west/north/east/south): ").strip().lower()
        loc = self.current_location
        if direction == "current":
            c = ", ".join([cr.nickname for cr in loc.creatures if cr is not self]) or "no creatures"
            i = ", ".join([it.name for it in loc.items]) or "no items"
            print(f"In this area, you see {c} and {i}.\n")
            return
        if direction not in loc.doors or not loc.doors[direction]:
            print("This direction leads nowhere.\n")
            return
        target = loc.doors[direction]
        c = ", ".join([cr.nickname for cr in target.creatures]) or "no creatures"
        i = ", ".join([it.name for it in target.items]) or "no items"
        print(f"In the {direction}, there seems to be {target.name} with {i} and {c} nearby.\n")

    # Race 
    def challenge(self, opp_name):
        loc = self.current_location
        opp = next((c for c in loc.creatures if c is not self and c.nickname.lower() == opp_name.lower()), None)
        if not opp:
            print("No such creature here.\n")
            return self

        # Allow challenge even if creature not adoptable
        if not opp.adoptable:
            if random.random() < 0.7:
                print(f"The wild {opp.nickname} seems hesitant... but accepts your challenge!\n")
                opp.adoptable = True
            else:
                print(f"The {opp.nickname} just ignored you.\n")
                return self

        print(f"\nRace started: {self.nickname} vs {opp.nickname} (100 meters)")
        dist_a = dist_b = 100
        sec = 0
        while dist_a > 0 and dist_b > 0:
            sec += 1
            hop_a = self.base_speed * (1 + luck_factor_percent() / 100)
            hop_b = opp.base_speed * (1 + luck_factor_percent() / 100)
            if self.pogo_active:
                hop_a *= 2
            dist_a = max(0, dist_a - hop_a)
            dist_b = max(0, dist_b - hop_b)
            print(f"{self.nickname} hopped {hop_a:.2f} m. Remaining: {dist_a:.2f}")
            print(f"{opp.nickname} hopped {hop_b:.2f} m. Remaining: {dist_b:.2f}\n")
            time.sleep(1)

        self.pogo_active = False

        # Determine result and handle outcomes
        if dist_a <= 0 and dist_b <= 0:
            print(f"Both reached finish line in {sec}s — draw!\n")
            result = "Draw"
        elif dist_b <= 0:
            print(f"{opp.nickname} reached finish line in {sec}s! You lose!\n")
            self.energy -= 1
            result = "Lose"
            if self.energy <= 0:
                print(f"{self.nickname} exhausted and released into the wild!\n")
                if not self.pets:
                    print("Game Over — no more Pymons!\n")
                    sys.exit(0)
                new = self.pets.pop(0)
                new.inventory.extend(self.inventory)
                print(f"{new.nickname} becomes your new Pymon.\n")
                self.log_race_result(opp.nickname, result)
                return new
        else:
            print(f"{self.nickname} reached finish line in {sec}s! You win!\n")
            result = "Win"
            loc.remove_creature(opp)
            opp.set_location(None)
            self.pets.append(opp)
            print(f"Captured Pymon: {opp.nickname} added to bench.\n")

        # Record race result to race_stats.txt 
        try:
            from datetime import datetime
            ts = datetime.now().strftime("%d/%m/%Y %I:%M%p")
            with open("race_stats.txt", "a", encoding="utf-8") as f:
                f.write(f"Race: {self.nickname} vs {opp.nickname} — {result} ({ts})\n")
            print(f"Race result recorded in race_stats.txt ({result}).\n")
        except Exception as e:
            print(f"(Warning: could not log race result: {e})\n")

        return self

# Class: Record
# Handles all CSV file imports for locations, creatures, and items.
# centralises file I/O and data parsing logic.
class Record:
    def __init__(self):
        self.locations, self.creatures, self.items = [], [], []
        self._loc = {}

    @staticmethod
    def _norm(s): return (s or "").strip()
    @staticmethod
    def _truthy(s): return str(s).strip().lower() in ("true","t","yes","y","1")

    def import_locations(self, path):
        """Loading locations from CSV and connect doors correctly."""
        try:
            with open(path, newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                headers = next(reader, None)  # skip header if exists
                rows = [r for r in reader if r and r[0].strip()]

            # First pass: create all Location objects 
            for r in rows:
                name = r[0].strip()
                desc = r[1].strip() if len(r) > 1 else ""
                loc = Location(name, desc)
                self.locations.append(loc)
                self._loc[name] = loc

            # Second pass: connect doors by name 
            for r in rows:
                name = r[0].strip()
                loc = self._loc.get(name)
                if not loc:
                    continue

                # read door names 
                west  = r[2].strip() if len(r) > 2 and r[2] else None
                north = r[3].strip() if len(r) > 3 and r[3] else None
                east  = r[4].strip() if len(r) > 4 and r[4] else None
                south = r[5].strip() if len(r) > 5 and r[5] else None

                if west  and west  in self._loc: loc.doors["west"]  = self._loc[west]
                if north and north in self._loc: loc.doors["north"] = self._loc[north]
                if east  and east  in self._loc: loc.doors["east"]  = self._loc[east]
                if south and south in self._loc: loc.doors["south"] = self._loc[south]

        except Exception as e:
            raise InvalidInputFileFormat(f"Invalid locations file: {e}")

    def import_creatures(self, path):
        """Load creatures from CSV and place them on the correct locations if available."""
        try:
            with open(path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    n = self._norm(row.get("nickname") or row.get("name"))
                    if not n:
                        continue
                    d = self._norm(row.get("description"))
                    ad = self._truthy(row.get("adoptable"))
                    sp = int(row.get("speed") or 5)

                    # Look for a location column in CSV
                    loc_name = self._norm(row.get("location"))
                    if loc_name and loc_name in self._loc:
                        l = self._loc[loc_name]
                    else:
                        l = random.choice(self.locations) if self.locations else None

                    c = Creature(n, d, l, ad, sp)
                    if l:
                        l.add_creature(c)
                    self.creatures.append(c)
        except Exception as e:
            raise InvalidInputFileFormat(f"Invalid creatures file: {e}")


    def import_items(self, path):
        """Load items from CSV and place them in correct locations ."""
        try:
            with open(path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name = self._norm(row.get("name"))
                    if not name:
                        continue
                    desc = self._norm(row.get("description"))
                    pickable = self._truthy(row.get("pickable"))
                    consumable = self._truthy(row.get("consumable"))
                    loc_name = self._norm(row.get("location") or row.get("location_name"))

                    it = Item(name, kind="generic", description=desc,
                              pickable=pickable, consumable=consumable)
                    self.items.append(it)

                    # Correctly assign items 
                    loc = self._loc.get(loc_name)
                    if loc:
                        loc.add_item(it)
                    else:
                        random.choice(self.locations).add_item(it)
        except Exception as e:
            raise InvalidInputFileFormat(f"Invalid items file: {e}")


    def get_locations(self):
        return self.locations

# Class: Operation
# High-level game controller.
# Coordinates player actions, menu interface, and admin utilities.
class Operation:
    def __init__(self):
        self.record = Record()
        self.player = Pymon()

    def setup(self, loc_file, cre_file, item_file):
        # Load world data from CSVs
        self.record.import_locations(loc_file)
        self.record.import_creatures(cre_file)  # random placement
        self.record.import_items(item_file)     # robust item placement

        # Random starting location
        start = random.choice(self.record.get_locations())
        self.player.spawn(start)

        print("\nWelcome to Pymon World")
        print("It's just you and your loyal Pymon roaming around to find more Pymons to capture and adopt.\n")
        print(f"You started at {start.name.lower()}\n")

    def show_stats(self):
        print("\n----- Current Stats -----")
        print(f"Energy: {self.player.energy}/3")
        print(f"Inventory items: {len(self.player.inventory)}")
        print(f"Captured Pymons: {len(self.player.pets)}")
        print("-------------------------\n")

    def save_game(self):
        with open("game_save.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Pymon", self.player.nickname])
            writer.writerow(["Energy", self.player.energy])
            inv = "|".join(i.name for i in self.player.inventory)
            writer.writerow(["Inventory", inv])
            writer.writerow(["Location", self.player.current_location.name])
        print("Game saved to game_save.csv\n")

    def load_game(self):
        try:
            with open("game_save.csv", newline="") as f:
                reader = csv.reader(f)
                data = {rows[0]: rows[1] for rows in reader}
            loc_name = data.get("Location", "")
            loc = next((l for l in self.record.locations if l.name.lower() == loc_name.lower()), None)
            if loc:
                self.player.spawn(loc)
            print("Game loaded successfully.\n")
        except Exception as e:
            print(f"⚠️ Error loading game: {e}\n")

    def add_location(self):
        name = input("Enter new location name: ").strip()
        desc = input("Enter description: ").strip()
        self.record._loc[name] = Location(name, desc)
        self.record.locations.append(self.record._loc[name])
        with open("locations-2.csv", "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([name, desc, "", "", "", ""])
        print(f"Location '{name}' added and saved.\n")

    def add_creature(self):
        name = input("Enter creature name: ").strip()
        desc = input("Enter description: ").strip()
        adopt = input("Adoptable? (yes/no): ").strip().lower() in ("yes", "y", "true", "1")
        c = Creature(name, desc, adoptable=adopt)
        random.choice(self.record.locations).add_creature(c)
        with open("creatures.csv", "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([name, desc, "yes" if adopt else "no", "5"])
        print(f"Creature '{name}' added and placed randomly.\n")

    def randomise_map(self):
        for l in self.record.locations:
            for d in l.doors:
                if random.random() < 0.3:
                    l.doors[d] = None
                else:
                    l.doors[d] = random.choice(self.record.locations)
        print("Map connections randomised.\n")

    def show_menu(self):
        while True:
            print("\nPlease issue a command to your Pymon:")
            print("=======================================")
            print("1) Inspect Pymon")
            print("2) Inspect current location")
            print("3) Move")
            print("4) Pick Item")
            print("5) View Inventory")
            print("6) Challenge Creature")
            print("7) Generate Stats")
            print("8) Save Game")
            print("9) Load Game")
            print("10) Add Location")
            print("11) Add Creature")
            print("12) Randomise Map")
            print("13) Exit the program")
            print("=======================================")

            ch = input("Enter command (1–13): ").strip()

            if ch == "1":
                self.player = self.player.inspect()
            elif ch == "2":
                self.player.current_location.describe()
            elif ch == "3":
                valid = {"west", "north", "east", "south"}
                while True:
                    d = input("Moving to which direction? (west/north/east/south): ").lower()
                    if d in valid:
                        break
                    print("Invalid direction. Please enter west, north, east, or south.\n")
                self.player = self.player.move(d)
            elif ch == "4":
                self.player.pick_item()
            elif ch == "5":
                self.player.show_inventory()
            elif ch == "6":
                loc = self.player.current_location
                others = [c.nickname for c in loc.creatures if c is not self.player]
                if not others:
                    print("No other creatures here.\n")
                    continue
                for o in others:
                    print(f" - {o}")
                n = input("Challenge which creature?: ").strip()
                self.player = self.player.challenge(n)
            elif ch == "7":
                self.show_stats()
            elif ch == "8":
                self.save_game()
            elif ch == "9":
                self.load_game()
            elif ch == "10":
                self.add_location()
            elif ch == "11":
                self.add_creature()
            elif ch == "12":
                self.randomise_map()
            elif ch == "13":
                print("Exiting game... Goodbye!")
                break
            else:
                print("Invalid choice. Please try again.\n")

 
    def save_game(self, fname="gamesave2025.csv"):
        with open(fname, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["nickname", "energy", "location", "inventory"])
            inv = "|".join(i.name for i in self.player.inventory)
            loc = self.player.current_location.name if self.player.current_location else ""
            w.writerow([self.player.nickname, self.player.energy, loc, inv])
            # also save bench pymons
            for p in self.player.pets:
                inv2 = "|".join(i.name for i in p.inventory)
                loc2 = p.current_location.name if p.current_location else ""
                w.writerow([p.nickname, p.energy, loc2, inv2])
        print(f"Game saved to {fname}\n")

    def load_game(self, fname="gamesave2025.csv"):
        if not os.path.exists(fname):
            print("No save file found.\n")
            return
        with open(fname, newline="", encoding="utf-8") as f:
            r = csv.DictReader(f)
            rows = list(r)
        if not rows:
            print("Empty save file.\n")
            return
        first = rows[0]
        loc = next((l for l in self.record.locations if l.name == first["location"]), None)
        self.player = Pymon(first["nickname"])
        self.player.energy = int(first["energy"])
        self.player.spawn(loc)
        for nm in first["inventory"].split("|"):
            if nm:
                self.player.inventory.append(Item(nm, "", nm, True))
        print("Game loaded successfully!\n")

    def record_race_result(self, opponent, result, path="race_stats.txt"):
        from datetime import datetime
        ts = datetime.now().strftime("%d/%m/%Y %I:%M%p")
        line = f'{self.player.nickname} vs {opponent} — {result} at {ts}\n'
        with open(path, "a", encoding="utf-8") as f:
            f.write(line)
        print(f"Race recorded: {line.strip()}\n")
    def add_location(self):
        name = input("Enter new location name: ")
        desc = input("Enter description: ")
        with open("locations-2.csv", "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow([name, desc, None, None, None, None])
        print(f"Location '{name}' added to file.\n")

    def add_creature(self):
        name = input("Enter creature name: ")
        desc = input("Enter description: ")
        with open("creatures.csv", "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow([name, desc, "yes", 5])
        print(f"Creature '{name}' added to file.\n")

    def randomise_connections(self):
        locs = self.record.get_locations()
        for l in locs:
            for d in ("west", "north", "east", "south"):
                if random.random() < 0.5:
                    l.doors[d] = random.choice(locs)
        print("Connections randomised!\n")

if __name__ == "__main__":
    # Automatically detect CSVs in the same folder 
    base = os.path.dirname(os.path.abspath(__file__))
    loc = os.path.join(base, "locations-2.csv")
    cre = os.path.join(base, "creatures.csv")
    itm = os.path.join(base, "items.csv")

    # Verify that required files exist in the same folder
    missing = [f for f in [loc, cre, itm] if not os.path.exists(f)]
    if missing:
        print("⚠️ Error: Missing one or more CSV files in the same folder as prog2.py:")
        for f in missing:
            print(f" -", os.path.basename(f))
        print("\nPlease ensure that 'locations-2.csv', 'creatures.csv', and 'items.csv' are in the same directory as prog2.py.")
        sys.exit(1)

    print(f"(Auto-loading defaults: {os.path.basename(loc)}, "
          f"{os.path.basename(cre)}, {os.path.basename(itm)})\n")

    # Launch the game
    g = Operation()
    g.setup(loc, cre, itm)
    g.show_menu()