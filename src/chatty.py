import socket
import threading
from time import sleep as sleep

chatPort=1435

#recieves messages and handles connections
class serverPart(threading.Thread):
    #self.socket - socket listens
    #self.messageQueue - text IO
    #self.contacts - current connections
    #self.stop - boolean
    
    def __init__(self,parser):
        super().__init__()
        self.parser = parser
        self.socket=None
        self.messageQueue = []
        self.contacts = {}
        self.stop = False
        

    def listen(self):
        self.socket = socket.socket()
        host = socket.gethostname()
        self.socket.bind((host,chatPort))
        self.socket.setblocking(False)
        self.socket.listen(8)

        print("creating server on "+str(socket.gethostbyname(socket.gethostname()))+", port "+str(chatPort))  
    
    def close(self):
        self.socket.close()
        for key in self.contacts.keys():
            self.contacts[key].close()

    def queueMessage(self,message):
        #sending messages to contacts
        print("(queueing)<<"+message)
        self.messageQueue.append(message)
    
    def addConnection(self,ip,newSocks=None):
        if(newSocks==None):
            newConnection = socket.socket()
            if not ip in self.contacts.keys():
                try:
                    newConnection.connect((ip,chatPort))
                    newConnection.setblocking(False)
                    self.contacts[ip]=newConnection
                    print("added connection at "+ip)
                except socket.error:
                    print("failed at make new connection to "+ip)
            else:
                print("connection already exists")
        else:
            newSocks.setblocking(False)
            self.contacts[ip]=newSocks
    
    def stopThread(self):
        self.stop=True;
    
    def run(self):
        while not self.stop:
            
           #sending messages
            for message in self.messageQueue:
                for ip in self.contacts.keys():
                    print("attempting to send message \""+message+" from queue to "+ip)
                    self.contacts[ip].send(bytes(message, 'UTF-8'))
                self.messageQueue.remove(message)
            
            #recieving messages
            for ip in self.contacts.keys():
                try:
                    incomingMessage = self.contacts[ip].recv(2095)
                    print(incomingMessage);
                    self.parser.parseMessage(incomingMessage)
                except socket.error: # if there is no message
                    pass
            
            #recieving new peers
            try:
                for newConnection in iter(lambda: self.socket.accept(), ""):
                    print("now recieving connection from "+newConnection[1][0]+"..")
                    print(newConnection)
                    self.addConnection(newConnection[1][0],newConnection[0])
            except socket.error: # if there are no new peers
                pass
            
            
#pipes messages to server, which echoes them to connections
class clientPart(threading.Thread):
    #socket - socket
    #messages- textIO
    #username - string
    #stop - boolean
    
    def __init__(self,server,parser,username = "Anonymous"):
        super().__init__()
        self.server = server
        self.parser = parser
        self.socket = None
        self.messages = []
        self.username = username
        self.stop = False
               
    def connectToHost(self,ip):
        s = socket.socket()
        s.connect((ip,chatPort))
        self.socket = s
    
    def stopThread(self):
        self.stop=True;
    
    def run(self):
        while not self.stop:
            #get messages, parse them, send them to server
            a = input()
            if(len(a)>=1):
                if(a[0]!="/"):
                    a= "/say "+self.username+" "+a
                self.parser.parseMessage(self,self.server,a)
            sleep(0.5)

class transformer(threading.Thread):
    def __init__(self):
        self.chatfunctions = {
                         "/say"         :self.parseSay,
                         "/me"          :self.parseLocalMe,
                         "/meF"         :self.parseForeignMe,
                         "/self"        :self.getIP,
                         "/add"         :self.parseConnect,
                         "/connect"     :self.parseConnect,
                         "/connections" :self.displayConnections,
                         "/peers"       :self.displayConnections,      
                         "/queue"       :self.displayQueue,
                         "/close"       :self.parseClose,
                         "/stop"        :self.parseClose,
                         "/quit"        :self.parseClose
                         }

    def parseMessage(self,client,server,message):
        try:
            args = message.split()
            if ( args[0] in self.chatfunctions.keys() and self.chatfunctions[args[0]](client,server,args[1:]) ):
                server.queueMessage(message)
            elif (not args[0] in self.chatfunctions.keys()):
                print(args[0]+" is not a valid command")
            
        except IndexError:
            print("some shit went wrong with the args")
    
    #commands
    #take self, client, server, [messages]
    #return True if the message should continue on to the server
    def parseSay(self,client,server,messages):
        message = "";
        for i in range(1,len(messages)):
            message+=messages[i]+" "
        print (messages[0]+": "+message)
        return True
    
    def parseLocalMe(self,client,server,messages):
        message = "";
        for i in range(len(messages)):
            message+=messages[i]+" "
        print (client.username+" "+message)
        server.queueMessage("/meF "+client.username+" "+message)
        return False
    
    def parseForeignMe(self,client,server,messages):
        message = "";
        for i in range(1,len(messages)):
            message+=messages[i]+" "
        print (messages[0]+" "+message)
        return True
    
    def getIP(self,client,server,messages):
        print(client.username +" at "+
              str(server.socket.getsockname()[0]) +":"+
              str(server.socket.getsockname()[1]))
        return False
    
    def parseConnect(self,client,server,messages):
        server.addConnection(messages[0])
        return False
    
    def parseClose(self,client,server,messages):
        print("quitting...")
        server.close
        client.stopThread()
        server.stopThread()
        print("now closed.")
        return False
    
    def displayConnections(self,client,server,args):
        if(len(server.contacts)>0):
            for contact in server.contacts.keys():
                print(contact+"  "+str(server.contacts[contact]));
        else:
            print("Fatty fatty, no connections")
        return False
    
    def displayQueue(self,client,server,args):
        print(server.messageQueue)
        return False
    
def main():
    print("#####################################")
    print("#       IT'S CHATTY, BITCHES        #")
    print("# --------------------------------- #")    
    print("# Untested and unapproved by anyone #")
    print("#                                   #")
    print("#####################################")
    
    parser = transformer()
    server = serverPart(parser)
    client = clientPart(server, parser)
    
    client.start()
    try:
        server.listen()
    except socket.error:
        print("could not bind server. is another instance running?")
        print("now quitting.")
        client.stopThread()
        return
    server.start()
    
    

main()
