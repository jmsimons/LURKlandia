import struct
from time import sleep

class LURKprot:

    def __init__(self, conn = None):
        
        from LURKprot_keys import error_key, message_types, message_key

        self.version = '2.2'
        self.conn = conn
        self.error_key = error_key
        self.message_types = {v:k for k,v in message_types.items()}
        self.message_key = message_key

    def set_conn(self, conn):
        self.conn = conn

    def decode(self, conn = None): ## Uses self.message_key to decode server messages, returns a message dictionary ##
        if not conn: conn = self.conn
        data = conn.recv(1)
        # print(data)
        if data not in (b'', None, 0):
            mes_type = struct.unpack('<B', data)[0]
            # print('Message Type:', mes_type)
            # if mes_type == 3: return message_dict
            if mes_type not in self.message_key:
                return None
            message_dict = {'type': mes_type}
            reference = self.message_key[mes_type]
            for key in reference['order']:
                length = reference[key][0]
                if not length:
                    length = message_dict['length']
                    format = reference[key][1].format(length)
                else: format = reference[key][1]
                data = conn.recv(length)
                if not data: return None
                value = struct.unpack(format, data)
                # print('Value:', value, '\n', 'has length:', len(value))
                if len(value) == 1: value = value[0]
                elif len(value) > 1: value = ''.join([chr(i) for i in value if i])
                else: value = ''
                message_dict[key] = value
            print('Incoming: ', message_dict)
            return message_dict
        else:
            print('Problem Data:', data)
        return None

    def encode(self, message_dict, conn = None): ## Uses self.message_key to encode message for server from a message dictionary ##
        if not conn: conn = self.conn
        print('Outgoing: ', message_dict)
        mes_type = message_dict['type']
        reference = self.message_key[mes_type]
        message = bytes([mes_type])
        for key in reference['order']:
            format_key = reference[key]
            if key != 'length': value = message_dict[key]
            else: value = len(message_dict['text'])
            value_type = type(value)
            # print(value)
            if value_type == int:
                if format_key[0]:
                    if format_key[0] == 1: message += bytes([value])
                    elif format_key[0] == 2: message += struct.pack(format_key[1], value)                            
                else:
                    format = format_key[1].format(message_dict['length'])
                    message += struct.pack(format, value)
            elif value_type == str:
                if key == 'text': message += bytes(value, 'UTF-8')
                else:
                    message += bytes(value, 'UTF-8')[:31]
                    message += bytes(32 - len(value))
        return message
        conn.send(message)

    def search_type(self, message_dict):
        for k, v in self.message_key:
            if sorted(v['order']) == tuple(sorted(message_dict.keys())):
                message_dict['type'] = k
                self.encode(message_dict)

    def get_char_message(self, char_dict):
        char_dict['type'] = self.message_types['Character']
        return char_dict

    def get_chat_message(self, sender, target, text):
        message_dict = {'type': self.message_types['Chat'],
                        'sender': sender,
                        'text': text,
                        'recipient': target}
        return message_dict
    
    def get_err_message(self, code, text = None):
        message_dict = {'type': self.message_types['Error'],
                        'code': code}
        message_dict['text'] = text if text else self.error_key[code]
        return message_dict

    def get_cur_room_message(self, room_dict):
        room_dict['type'] = self.message_types['Current Room']
        return room_dict
    
    def get_con_room_message(self, room_dict):
        room_dict['type'] = self.message_types['Connecting Room']
        return room_dict