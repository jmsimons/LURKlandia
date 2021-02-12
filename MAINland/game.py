from game_components import Character, Room, Loot
# from models import Session, Room, Connection, Monster, Loot
from player import Player
from LURKp import LURKprot
from random import randint
import queue, threading, time, models

class Game:

    def __init__(self):

        self.settings = {
            'landlord': 'Mr. Rowanitz',
            'start_stat_limit': 100,
            'start_room': 1,
            'returning_room': 5,
            'stash_player_after': 600
        }

        self.actions = {
            2: self.change_room,
            3: self.stage_fight,
            4: self.stage_pvp_fight,
            5: self.loot,
            6: self.start_player,
            12: self.stash_player
        }

        self.rooms = {}
        self.players = {}
        self.queue = queue.Queue() # Queue of dictionaries to process in game_loop #
        self.remove = queue.Queue() # Queue of Player objects to stash on socket error #
        self.load_map()
        self.lurk = LURKprot()
        self.thread = threading.Thread(target = self.game_loop)
        self.thread.start()

    def load_map(self): ### Loads Rooms, Connections, Monsters, and Lootables from database ###
        session = models.Session()
        rooms = session.query(models.Room).all()
        connections = session.query(models.Connection).all()
        monsters = session.query(models.Monster).all()
        lootables = session.query(models.Loot).all()
        for room in rooms:
            number, name, desc = room.id, room.name, room.description
            self.rooms[number] = Room(number, name, desc)
        for connection in connections:
            room1, room2 = connection.room1, connection.room1
            self.rooms[room1].connections.append(room2)
        for monster in monsters:
            name, attack, defense, regen, health, gold, room, desc = monster.name, monster.attack, monster.defense, monster.regen, monster.health, monster.gold, monster.room, monster.description
            self.rooms[room].monsters[name] = Character(name, attack, True, True, True, True, True, defense, regen, health, gold, room, desc)
        for lootable in lootables:
            room, name, value, rewards, message = lootable.room, lootable.name, lootable.value, lootable.rewards, lootable.message
            self.rooms[room].lootables.append(Loot(room, name, value, rewards, message))
    
    def game_loop(self):
        while True:
            game_queue_size = self.queue.qsize()
            if game_queue_size: print('Processing', game_queue_size, 'actions...')
            for _ in range(game_queue_size):
                action = self.queue.get() # Return a tuple of (player.name, message_dict)
                action_type = action[1]['type']
                self.route[action_type](action)
            remove_queue_size = self.remove.qsize()
            if remove_queue_size: print('Processing', remove_queue_size, 'removals...')
            for _ in range(remove_queue_size):
                player, time_added = self.remove.get()
                if time.time() - time_added >= self.settings['stash_player_after']:
                    self.stash_player((player, {}))

    def new_conn(self, conn): ### Passes conn to static method LURKprot.decode(), returns success or failure on player creation ###
        message_dict = LURKprot.decode(conn = conn)
        if message_dict and 'type' in message_dict and message_dict['type'] == 10:
            self.new_player(conn, message_dict)
            return True
        else:
            return False

    def new_player(self, conn, characer_dict): ### Checks availability of name or innactive Player object, creates/updates Player or responds with error message ###
        name = characer_dict['name']
        if name in self.players:
            try: players[name].conn.send(bytes(1)) # attempt writing to the socket to see if it's alive
            except:
                print('Found existing player with broken conn, replacing conn...')
                self.players[name].conn = conn
                return
            error_message = self.lurk.get_err_message(2)
            self.lurk.encode(error_message, conn = conn)
        # elif player in database: # This will check long-term player storage
        else:
            stats_total = sum(characer_dict['attack'], characer_dict['defense'], characer_dict['regen'])
            stats_limit = self.settings['start_stat_limit']
            if stats_total == stats_limit:
                self.players[name] = Player(self, conn, characer_dict = characer_dict)
            else:
                for stat in ('attack', 'defense', 'regen'): # recalculates each stat as a ratio and multiplies it by the game stat limit #
                    characer_dict[stat] = characer_dict[stat] / stats_total * stats_limit
                stats_total = sum(characer_dict['attack'], characer_dict['defense'], characer_dict['regen'])
                stats_delta = stats_limit - stats_total
                print(stats_delta)
                for i in [i for i in range(stats_delta)][::-1]:
                    for stat in ('attack', 'defense', 'regen'):
                        if not i: break
                        characer_dict[stat] += 1 * (i / abs(i))
                self.players[name] = Player(self, conn, characer_dict = characer_dict)

    def start_player(self, action): ### Updates player.character to indicate 'started' and adds player to the appropriate room ###
        name, message_dict = action
        player = self.players[name]
        player.character.started = True
        player.character.room = self.settings['start_room']
        self.rooms[self.settings['start_room']].append(name)

    def stash_player(self, action): ### Removes Player object from players and current room, adds or updates player record in long-term storage ###
        name, message_dict = action
        fair_well = self.lurk.get_chat_message(self.settings['landlord'], name, 'Sad to see you going so sooooon. Fair well!')
        self.players[name].send_queue.put(fair_well)
        self.players[name].character.started = False
        self.players[name].character.ready = False
        self.players[name].active = False
    
    def change_room(self, action): ### Checks that new room is a connection of current room, removes player from current room and adds to new room ###
        name, message_dict = action
        player = self.players[name]
        new_room = message_dict['room']
        current_room = player.character['room']
        if new_room in self.rooms[current_room].connections:
            self.rooms[current_room].remove(player)
            self.update_room(current_room)
            self.rooms[new_room].append(player)
            self.update_room(new_room)
            player.character.room = new_room

    def update_room(self, room): ### Sends updated characters, connections, and other info to all players in room ###
        current_room = self.rooms[room].get_dict()
        player_characters = [self.players[i].character.get_dict() for i in self.rooms[room].players]
        monster_characters = [i.get_dict() for i in self.rooms[room].monsters.values()]
        connecting_rooms = [self.rooms[i].get_dict() for i in self.rooms[room].connections.values()]
        for player in self.rooms[room].players:
            self.players[player].send_queue.put(current_room)
            for update_list in (player_characters, monster_characters, connecting_rooms):
                self.players[player].send_queue.put(update_list)

    def process_fight(self, room, players_list, monsters_list = None): ### Calculates attack and damage taken for each character's turn, finally calls self.update_room ###
        if monsters_list: # whole room fight
            for character in players_list: # Each player attacks first
                attack = character['attack']
                for character in monsters_list:
                    if character['health'] > 0:
                        calc_attack = randint(int(attack * 0.75), int(attack * 1.25)) # consider moving this above the for loop if functionality is slow #
                        damage_taken = calc_attack - character['defense']
                        self.rooms[room].monsters[character['name']].health -= damage_taken
            for character in monsters_list: # Then monsters attack
                attack = character['attack']
                for character in players_list:
                    calc_attack = randint(int(attack * 0.5), attack) # consider moving this above the for loop if functionality is slow #
                    damage_taken = calc_attack - character['defense']
                    self.players[character['name']].character.health -= damage_taken
        else: # pvp fight
            player1, player2 = players_list
            calc_attack = randint(int(player1['attack'] * 0.75), int(player1['attack'] * 1.25))
            damage_taken = calc_attack - player2['defense']
            self.players[player2['name']].character.health -= damage_taken
            calc_attack = randint(int(player2['attack'] * 0.75), int(player2['attack'] * 1.25))
            damage_taken = calc_attack - player1['defense']
            self.players[player1['name']].character.health -= damage_taken
        self.update_room(room)

    def stage_fight(self, action): ### Prepares character list for room, passes characters to calculate_attack ###
        name, message_dict = action
        room = self.players[name].character.room
        if self.rooms[room].monsters:
            players_list = self.rooms[room].players.copy()
            players_list.remove(name)
            players_list.insert(0, name)
            players_list = [self.players[i].character.get_fight_stats() for i in players_list]
            players_list = [i for i in players_list if i and i['health'] > 0]
            monsters_list = [i.get_fight_stats() for i in self.rooms[room].monster.values()]
            self.process_fight(room, players_list, monsters_list)
        else:
            message_dict = self.lurk.get_err_message(3)
            self.players[name].send_queue.put(message_dict)
    
    def stage_pvp_fight(self, action): ### Commences attack sequence, calculating attack and damage taken for each character's turn, and finally calls self.update_room ###
        name, message_dict = action
        target = message_dict['name']
        room = message_dict['room']
        if target in self.rooms[room].players:
            players_list = [name, target]
            players_list = [self.players[i].character.get_fight_stats() for i in players_list]
            self.process_fight(room, players_list)
        else:
            message_dict = self.lurk.get_err_message(6) #  text = 'Target player not in room'
            self.players[name].send_queue.put(message_dict)

    def loot(self, action):
        name, message_dict = action
        target = message_dict['name']
        if self.players[name].character.room == self.players[target].character.room:
            self.players[name].character.gold += self.players[target].character.gold
        else:
            message_dict = self.lurk.get_err_message(6)
            self.players[name].send_queue.put(message_dict)