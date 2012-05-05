import socket
import threading
import io

chatPort=1435

#recieves messages and handles connections
class serverPart(threading.Thread):
    #self.socket - socket listens
    #self.messageQueue - text IO
    #self.contacts - current connections
    
    def __init__(self,parser):
        super().__init__()
        self.parser = parser
        self.socket=None
        self.messageQueue = []
        self.contacts = {}

    def listen(self):
        self.socket = socket.socket()
        host = socket.gethostname()
        self.socket.bind((host,chatPort))
        self.socket.setblocking(False)
        self.socket.listen(8)

    def queueMessage(self,message):
        #sending messages to contacts
        print("(queueing)<<"+message)
        self.messageQueue.append(message)
    
    def addConnection(self,ip):
        newConnection = socket.socket()
        if not ip in self.contacts.keys():
            try:
                newConnection.connect((ip,chatPort))
                self.contacts[ip]=newConnection
            except socket.error:
                print("failed at make new connection to "+ip)
    
    def run(self):
        while True:
            #get new connections
            try:
                for connection in iter(lambda: self.socket.accept(), ""):
                    print (connection)
                    if not connection[1] in self.contacts.keys():
                        connection[0].setblocking(False)
                        print("adding connection to "+str(connection[1]))
                        self.contacts[connection[1]]=connection[0]
            except socket.error:
                pass
                #print("sockets suck")
            #sending/(recieving & parsing) messages and dropping broken connections
            for ip in self.contacts.keys():
                try:
                    #sending
                    for message in self.messageQueue:
                        self.contacts[connection].send(message)
                    #recieving
                    incomingMessage = self.contacts[connection].recv(2095)
                    self.parser.parseMessage(incomingMessage)
                except socket.error:
                    pass
                    #print("sockets suck too.")
            #clear list of messages - assume all have been sent
            del self.messageQueue[:]
            
#pipes messages to server, which echoes them to connections
class clientPart(threading.Thread):
    #socket - socket
    #messages- textIO
    #username - string
    
    def __init__(self,server,parser,username = "Anonymous"):
        super().__init__()
        self.server = server
        self.parser = parser
        self.socket = None
        self.messages = []
        self.username = username
               
    def connectToHost(self,ip):
        s = socket.socket()
        s.connect((ip,chatPort))
        self.socket = s
       
    def run(self):
        while True:
            #get messages, parse them, send them to server
            a = input()
            if(len(a)>=1):
                if(a[0]!="/"):
                    a= "/say "+self.username+" "+a
                self.parser.parseMessage(self,self.server,a)

class transformer(threading.Thread):
    def __init__(self):
        self.chatfunctions = {"/say" :self.parseSay,
                         "/me"  :self.parseLocalMe,
                         "/meF"  :self.parseForeignMe,
                         "/self" :self.getIP,
                         "/add":self.parseConnect,
                         "/connect":self.parseConnect,
                         "/connections":self.displayConnections,
                         "/queue":self.displayQueue}

    def parseMessage(self,client,server,message):
        print("parsing "+message)
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
    
    def displayConnections(self,client,server,args):
        print(server.contacts)
        return False
    
    def displayQueue(self,client,server,args):
        print(server.messageQueue)
        return False
    
def main():
    print("###################################")
    print("#       IT'S CHATTY, BITCHES      #")
    print("###################################")
    
    parser = transformer()
    server = serverPart(parser)
    client = clientPart(server, parser)
    
    client.start()
    server.listen()
    server.start()
    
    

main()
