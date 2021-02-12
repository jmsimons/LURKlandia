
# # # Module that initializes game map, manages socket connections, 

from game import Game
import socket, select, logging

host = socket.gethostname()
port = 5050

def setup_logging():
    FORMAT = '%(asctime)-15s %(clientip)s %(user)-8s %(message)s'
    logging.basicConfig(filename = f'LURK.log', level = logging.DEBUG)

def main(server_conn):
    game = Game()
    conns = [server_conn]
    new_conns = list()
    while True: ### The main process should only handle initial connections, passing subsequent messages into game ###
        print(f'Listening for conns: {new_conns}')
        for i in new_conns: conns.append(i)
        readers, _, _ = select.select(conns, [], []) #.extend(new_conns)
        for reader in readers:
            if reader == server_conn:
                conn, addr = server_conn.accept()
                print("New Client; Address:", addr, "Conn:", conn)
                logging.log("New Client; Address:", addr, "Conn:", conn)
                new_conns.append(conn)
            else:
                if game.new_conn(reader):
                    new_conns.remove(reader)

if __name__ == '__main__':
    setup_logging()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    while port <= 5054:
        try:
            s.bind((host, port))
            break
        except socket.error as e:
            print('Error binding port:', str(e))
        port += 1
    
    s.listen(5)
    print(f'Listening on port: {port}')
    main(s)
    