#import sys, os
#path_server = os.path.realpath(__file__)
#sys.path.append(os.path.dirname(path_server)+'/..')

import socket
import time
import _thread
from web_socket_server import SimpleWebSocketServer, WebSocket
from random import randint
import mysql.connector as sqlcon

def check_litteral(name):
    valid_char = ('a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z',
    'A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z','0','1','2','3','4','5','6','7','8','9')

    for char in name:
        if char not in valid_char:
            return False

    return True


class Server:
    def __init__(self):
        self.running = True
        self.prefixCmd=[]

    def on_msg(self):
        pass


class MultiClient(Server):
    def __init__(self, port_ws=18003):
        super().__init__()
        print('init multiclient')
        self.port_ws = port_ws
        self.clients = []
        self.last_client_id = 0

    def start(self):
        # "bug" can't change the ip or it stop working
        _thread.start_new_thread(self.loopWebsocketServer, ('', self.port_ws, ))
        #self.loopWebsocketServer('', self.port_ws)  
        self.loop_main()


    def loop_main(self):
        while True:
        #    pass
            time.sleep(5)


    def loopWebsocketServer(self, ip='', port=8000):
        web_socket_server = SimpleWebSocketServer(ip, port, WebsocketServer, game_server=self)
        print("Server WebSocket ip is %s, and port is %s" % (ip, port))
        while self.running:
            web_socket_server.serveonce()

    def on_new_client(self, new_client):
        new_client.id = self.last_client_id
        self.last_client_id += 1

        if new_client.server is None:
            new_client.server = self
        self.clients.append(new_client)
        self.send_msg("$ Bonjour bienvenue sur ce nouveau jeu qui testera votre intelligence.\n Le but est très simple: Finir la partie avevc un maximum de point. Le moyen est d ecrire et d envoyer des message.", new_client, verbose=True)

        self.send_msg("$ Pour commencer le jeu, veuillez nous donner un pseudonyme.", new_client, verbose=True)

        #self.send_msg('** You\'re connected on a server which ip is %s, and port is %s **' % (self.ip, self.port), new_client, verbose=True)

        return new_client

    def on_msg(self, msg, sender):
        if msg is not None and len(msg)>0:
            #msg = '>>' + msg
            print(msg)
            # give a response to any client connected
            self.send_msg(msg, sender)

    def send_msg(self, msg, dests, blacklist='', verbose=False, onePrint=True):
        if isinstance(dests, Client):
            # Transform the Client object into an iterable
            dests = [dests]

        firstPrint=True
        for dest in dests:
            if blacklist == '' or dest not in blacklist:
                if verbose and ((onePrint and firstPrint) or not onePrint):
                    print('System->%s:%s' % (dest.name, msg))
                    firstPrint=False
                dest.send(msg)


    def shutdown_client(self, client):
        self.clients.remove(client)
        client.shutdown()


class WebsocketServer(WebSocket):
    """ 
    Object from this class will create connection throught the web.
    And then create a WebsocketClient object, and bind it to his chat server. 
    """
    def __init__(self, server, sock, adress, game_server=None):
        super().__init__(server, sock, adress)
        self.game_server = game_server
        self.game_client = None

    def handleMessage(self):
        if self.game_client is not None:
            self.game_client.receive(self.data)

    def handleConnected(self):
        new_client = Psychoz(self)
        self.game_client = self.game_server.on_new_client(new_client)
        
    def handleClose(self):
        print("Someone left")

    def send(self, msg):
        self.sendMessage(msg)


class Client:
    def __init__(self, name='Unnamed', server=None):
        self.running = True
        self.name = name
        self.server = server

    def shutdown(self):
        del self

    def receive(self, msg):
        self.server.on_msg(msg, self)


class WebsocketClient(Client):
    def __init__(self, websocket,  name='Unnamed', server=None):
        super().__init__(name, server)
        self.websocket = websocket

    def send(self, msg):
        self.websocket.send(msg)


class Psychoz(WebsocketClient):
    def __init__(self, websocket, name='Unnamed', server=None):
        super().__init__(websocket, name, server)
        self.client=0
        self.events = []
        self.points = 0
        self.pseudo = "Unnamed"
        self.nb_input = 0
        self.start_time = time.time()
        self.last_event = "name"
        self.db=sqlcon.connect(host="127.0.0.1", user="user", passwd="root")
        self.game=0
        

    def receive(self, msg):
        print("get " + self.pseudo + " msg" + msg)
        print(self.game, self.client)
        if self.last_event == "name":
            self.server.on_msg(msg, self)
            
            
            if msg is not None and len(msg) > 3:
                # Maybe use a sort of database to keep track of past try on the "game".
                # Need unique pseudonyme.
                self.pseudo = msg
                self.send_to_client("$ Merci, que le jeu commence, sois le meilleur "+msg + ".")
                self.last_event = "start"
                try:
                    
                    cur = self.db.cursor(buffered=True)
                    cur.execute("USE theiqgame")
                    cur.execute("SELECT * FROM client")
                    number_of_rows = cur.rowcount
                    self.client=number_of_rows
                    print(number_of_rows)
                    cur.execute("INSERT INTO client(pseudo,client_id) VALUES (\""+msg+"\",\""+str(number_of_rows)+"\")")
                    cur.close()
                    self.db.commit()
                except sqlcon.Error as error:
                    print("Error: {}".format(error))
            else:
                self.send_to_client("$ S'il vous plait entrez un pseudonyme correct, au moins 4 caractères.")

        elif self.last_event == "strategy":
            print("strategie")
            self.send_to_client("$ Merci d'avoir jouer")
            cur = self.db.cursor(buffered=True)
            cur.execute("USE theiqgame")
            indice=len(self.events)
            cur.execute("INSERT INTO client(strategie) VALUES (\""+self.events[indice-1]+"\")")
            cur.close()
           
        

        elif self.last_event == "end":
            print("end")
                
            if msg is not None and len(msg) > 1:
                print("OK:" + msg)
                if msg[1].upper() == "O":
                    # The player wants to replay
                    self.last_event = "replay"
                    self.send_to_client("$ Que le jeu REcommence.")
                    self.nb_input = 0
                    try:
                        cur = self.db.cursor(buffered=True)
                        cur.execute("USE theiqgame")
                        cur.execute("SELECT * FROM game")
                        number_of_rows = cur.rowcount
                        self.game=number_of_rows
                        cur.execute("INSERT INTO game(client_id,game_id) VALUES ("+str(self.client)+","+str(self.game)+")")
                        cur.close()
                        self.db.commit()
                    except sqlcon.Error as error:
                        print("Error: {}".format(error))
                        
                elif msg[1].upper() == "N":
                    self.last_event = "strategy"
                    self.send_to_client("$ Qu'elle était votre stratégie pour ce jeu?")


        elif self.last_event != "end":
            msg = "[" + str(self.nb_input) + "] " +msg
            self.server.on_msg(msg, self)
            self.events.append(msg)
            self.nb_input += 1
            rand = randint(1,20)
            
            
            if rand <= 2 and self.nb_input > 3:
                # Game is finished
                self.last_event = "end"
                self.send_to_client("$ Vous avez terminé cette partie avec " + str(self.points) + " points en " + str(int(time.time()-self.start_time)) + " secondes")
                self.points = 0
                self.send_to_client("$ Voulez vous rejouer? (oui/non)")
                
            elif rand >= 8 and rand < 10:
                # Loose a point
                point = randint(1,7)
                self.points -= point
                self.send_to_client("$ Vous avez perdu "+ str(point)+" points. (vous avez actuellement " + str(self.points) + " points)")
                point=-point
            elif rand < 8 and rand > 2:
                # Win a point
                point = randint(1,10)
                self.points += point
                self.send_to_client("$ Vous avez gagné "+str(point)+" points. (vous avez actuellement " + str(self.points) + " points)")
            try:
                cur = self.db.cursor(buffered=True)
                cur.execute("USE theiqgame")
                cur.execute("INSERT INTO evenement(points,game_id,content) VALUES ("+str(point)+","+str(self.game)+",\""+str(self.events[-1])+"\")")
                cur.close()
                self.db.commit()
            except sqlcon.Error as error:
                print("Error: {}".format(error))
    def send_to_client(self, msg):
        
        self.websocket.send(msg)


if __name__ == '__main__':
    MultiClient().start()
