import socket
import select

MAX_MSG_SIZE = 1024
MAX_PENDING_CLIENTS = 10

class ChatServer():
    def __init__(self, host, port):
        self.host = host
        self.port = port
        # assuming 3 users here, who cares
        self.amazing_queue = {}

    def sendMessageToGroup(self, message, group):
        # Sends message to everyone but the source of the message
        for user in self.getUsersFromGroup(group):
        	    self.sendMessageToUser(message, user)

    def sendMessageToUser(self, message, user):
        if self.isOnline(user):
        	print 'Found %s online! Sending message' % user
        	self.send(message, user)
        else:
        	print '%s not online. Queueing message' % user
        	self.addMessageToQueue(message, user)


    def createUser(self, username):
        self.amazing_queue[username] = []

    def addMessageToQueue(self, message, user):
        self.amazing_queue[user].append(message)

    def getUserQueuedMessages(self, user):
        return '\n'.join(self.amazing_queue[user])

    def deliverMessages(self, user):
        print self.amazing_queue[user]
        try:
            self.send(self.getUserQueuedMessages(user), user)
            self.amazing_queue[user] = []
        except:
            print "Failed in deliverMessages()"

    def getUsers(self):
        return ['Johnny', 'Bravo', 'Dexter']

    def getUsersFromGroup(self, group_id):
        return ['victor', 'gabriel'] # Dexter is not there!
