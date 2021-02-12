

class Character:

    def __init__(self, name, alive, join, monster, started, ready, attack, defense, regen, health, gold, room, description):
        self.name = name
        self.alive = alive
        self.join = join
        self.monster = monster
        self.started = started
        self.ready = ready
        self.agro = 0 # 0-100, determines monster's likelihood of attacking without provocation, only used internally #
        self.attack = attack
        self.defense = defense
        self.regen = regen
        self.health = health
        self.gold = gold
        self.room = room
        self.description = description

    def get_flags(self):
        flags = 128 if self.alive else 0
        flags += 64 if self.join else 0
        flags += 32 if self.monster else 0
        flags += 16 if self.started else 0
        flags += 8 if self.ready else 0
        return flags
    
    def set_flags(self, flags):
        flags = f'{flags:08b}'
        self.join = bool(int(flags[1]))
    
    def get_dict(self): # Returns a character dictionary ready to pass into LURKprot.encode()
        return {
            'name': self.name,
            'flags': self.get_flags(),
            'attack': self.attack,
            'defense': self.defense,
            'regen': self.regen,
            'health': self.health,
            'gold': self.gold,
            'room': self.room,
            'text': self.description
        }
    
    def get_fight_stats(self):
        if self.join:
            return {
                'name': self.name,
                'attack': self.attack,
                'defense': self.defense,
                'regen': self.regen,
                'health': self.health
            }
        else: return None


class Room:

    def __init__(self, number, name, description): # Init with number and name only, append to connections, characters, and lootables #
        self.number = number
        self.name = name
        self.description = description
        self.connections = [] # list of integer room numbers #
        self.players = [] # list of player names #
        self.monsters = {} # list of monster names
        self.lootables = [] # list of lootable names

    def get_dict(self):
        dictionary = {
            'name': self.name,
            'number': self.number,
            'text': self.description
        }
        return dictionary


class Loot: # This will need to be some sort of protocal extension.

    def __init__(self, room, name, value, rewards, message):
        self.room = room
        self.name = name
        self.value = value # Gold
        self.rewards = rewards # Extra attack, defense, regen, or health
        self.message = message # A useful(or not so useful) clue