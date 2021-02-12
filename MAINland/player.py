import threading, select, pickle, os, struct, time
from LURKp import LURKprot
from game_components import Character


class Q:

    def __init__(self): ### Queue object that uses a threading Lock and bytes pipe file for put() and get() ###
        self.lock = threading.Lock()
        self.rq, self.wq = os.pipe() # Pipe returns two file descriptors, this class's fileno and read mothods reference self.fq, where the put method references self.wq #

    def put(self, item): ## writes 2-byte length for subsefquent pickle object written ##
        with self.lock:
            item = pickle.dumps(item)
            bytes_to_write = struct.pack('<h', len(item))
            print(bytes_to_write)
            os.write(self.wq, bytes_to_write)
            os.write(self.wq, item)

    def get(self): ## Reads 2-bytes for subsequent pickle object to read ##
        with self.lock:
            bytes_to_read = struct.unpack('<h', os.read(self.rq, 2))[0]
            print(bytes_to_read)
            data = os.read(self.rq, bytes_to_read)
            print(data)
            item = pickle.loads(data)
            return item

    def fileno(self):
        fno = self.rq
        return fno


class Player:

    def __init__(self, game_object, conn, character_dict = None, table_object = None):
        # !!! Never update self.character from within this class's thread, only from game thread !!! #
        if character_dict: self.add_from_dict(character_dict)
        elif table_object: self.add_from_table(table_object)
        else: return print('Player Creation Failure: Requires kwarg character_dict or table_object')
        self.conn = conn
        self.lurk = LURKprot(conn = conn)
        self.send_queue = Q()
        self.send_queue.put(self.character.get_dict())
        self.game = game_object
        self.thread = threading.Thread(target = self.conn_loop)
        self.active = True
        self.thread.start()

    def add_from_dict(self, character_dict):
        name = character_dict['name']
        flags = character_dict['flags']
        flags = f'{flags:08b}'
        join = bool(int(flags[1]))
        attack = character_dict['attack']
        defense = character_dict['defense']
        regen = character_dict['regen']
        health = character_dict['health']
        gold = character_dict['gold']
        description = character_dict['text']
        self.character = Character(name, True, join, False, False, True, attack, defense, regen, health, gold, room, description)

    def add_from_table(self, table_object):
        pass

    def conn_loop(self): ### Routes incoming message to other player or game queue, outgoing message to conn, or flags self.conn as broken ###
        while self.active:
            readers, writers, errors = select.select([self.conn], [self.send_queue], [self.conn]) # Writers should be a file which can be polled or watched
            for reader in readers:
                message_dict = self.lurk.decode(reader)
                print('Incoming from', self.name, self.message_dict)
                if message_dict['type'] == 1:
                    self.game.players[message_dict['recipient']].send_queue.put(message_dict)
                else:
                    self.game.queue.put((self.name, message_dict))
            for writer in writers:
                message_dict = writer.get()
                print('Outgoing to', self.name, self.message_dict)
                self.lurk.encode(message_dict)
            for error in errors:
                print('Error in', self.name, error)
                self.active = False
                self.game.remove.put((self.name, time.time()))
