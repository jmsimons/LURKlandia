from LURKconfig import game_settings
from player import Player
from LURKp import LURKprot
from math import ceil
import threading, time
import multiprocessing.dummy as mp

class ClientManager: ### Uses a threaded loop to relay messages between Game and Players ###

    def __init__(self, game_queue, client_queue):
        self.game_settings = game_settings
        self.lurk = LURKprot()
        self.players = {}
        self.game_queue = game_queue
        self.client_queue = client_queue
        self.thread = threading.Thread(target = self.message_loop)
        self.thread.start()

    def route_message(self, message):
        name, message_dict = message
        if name in self.players:
            self.players[name].send_queue.put(message_dict)
        else:
            print(f'Player Route Error: {name} not found')

    def message_loop(self):
        while True:
            message = self.client_queue.get()
            self.route_message(message)
            # print('Waiting for client queue')
            # client_queue_size = self.client_queue.qsize()
            # if client_queue_size:
            #     if client_queue_size > 100: client_queue_size = 100
            #     messages = [self.client_queue.get() for _ in range(client_queue_size)]
            #     pool_size = ceil(client_queue_size / 4)
            #     print('Routing', client_queue_size, 'messages with', pool_size, 'threads')
            #     with mp.Pool(pool_size) as pool:
            #         pool.map(self.route_message, messages)

    def greet_conn(self, conn):
        lurk_version = self.lurk.get_version_message()
        self.lurk.encode(lurk_version, conn = conn)
        greeting = self.lurk.get_game_message(self.game_settings['initial_points'], self.game_settings['stat_limit'], self.game_settings['greeting'])
        self.lurk.encode(greeting, conn = conn)

    def approve_conn(self, conn): ### Checks availability of name or innactive Player object, creates/updates Player or responds with error message ###
        message_dict = self.lurk.decode(conn = conn)
        if message_dict and 'type' in message_dict and message_dict['type'] == 10:
            name = message_dict['name']
            # print(f'Approval pending for: {name}')
            stats_total = message_dict['attack'] + message_dict['defense'] + message_dict['regen']
            if stats_total == self.game_settings['initial_points']:
                if name in self.players:
                    print("Attempting to resurrect")
                    if self.resurrect_player(conn, message_dict):
                        self.game_queue.put((name, message_dict))
                        return True
                else:
                    print(f'Adding new player: {name}')
                    self.players[name] = Player(self, name, conn)
                    self.game_queue.put((name, message_dict))
                    return True
            else:
                print(f"Rejecting character stats for {name}")
                text = f"Attack, defense, and regen must total {self.game_settings['initial_points']}"
                error_message = self.lurk.get_err_message(4, text = text)
                self.lurk.encode(error_message, conn = conn)
        return False
    
    def resurrect_player(self, conn, character_dict):
        name = character_dict['name']
        try: self.players[name].conn.send(bytes(1)) # attempt writing to the socket to see if it's alive
        except:
            print('Found existing player with broken conn, replacing conn...')
            self.players[name].new_thread(conn)
            return True
        print("Rejecting new conn")
        error_message = self.lurk.get_err_message(2)
        self.lurk.encode(error_message, conn = conn)
        return False