import socket
import select
from sets import Set
from random import choice
from string import ascii_uppercase

MAX_MSG_SIZE = 1024
MAX_PENDING_CLIENTS = 10

class GroupKeyError(Exception):
    def __init__(self, group_id):
        self.group_id = group_id
    def __str__(self):
        return "Group {} does not exist.".format(group_id)

class UserKeyError(Exception):
    def __init__(self, user_id):
        self.user_id = user_id
    def __str__(self):
        return "User {} does not exist.".format(user_id)

class GroupExists(Exception):
    def __init__(self, group_id):
        self.group_id = group_id
    def __str__(self):
        return "Group {} already exists.".format(group_id)

class GroupDoesNotExist(Exception):
    def __init__(self, group_id):
        self.group_id = group_id
    def __str__(self):
        return "Group {} does not exist.".format(group_id)

class ChatServer():
    def __init__(self, host, port):
        self.host = host
        self.port = port
        # assuming 3 users here, who cares
        self.amazing_queue = {} # lookup by username. Each will be a list.
        self.user_info = {} # lookup by username. Each will be a user_info dictionary.
        self.groups = {} # lookup by group id. Each will be a list
        self.logged_in_users = {} # lookup by session token.

    ##################################
    ### For server subclasses
    ##################################

    def username_exists(self, username):
        return username in self.amazing_queue

    def create_account(self, username, password, group_id = None):
        self.amazing_queue[username] = []
        self.user_info[username] = {
            'username': username,
            'password': password,
            'group_id': group_id,
            'logged_in': False,
            'session_token': 'QQQQQQQQQQQQ'
        }
        if group_id:
            if group_id not in self.groups:
                raise GroupKeyError(group_id)
            else:
                self.groups[group_id].add(username)
            self.groups[group_id]

    def create_group(self, group_id):
        if group_id in self.groups:
            raise GroupExists(group_id)
        else:
            self.groups[group_id] = []

    def login(self, username, password):
        if username not in self.user_info:
            return False, ''
        user = self.user_info[username]
        if user['password'] == password:
            user['logged_in'] = True
            user['session_token'] = ''.join(choice(ascii_uppercase) for i in range(12))
            self.logged_in_users[user['session_token']] = user
            return True, user['session_token']
        else:
            return False, ''

    ##################################
    ### Internal helpers
    ##################################

    def addUserToGroup(self, username, group_id):
        if group_id not in self.groups:
            raise GroupDoesNotExist
        else:
            user = self.user_info[username]
            self.groups[group_id].append(user)
            user['group_id'] = group_id

    def sendMessageToGroup(self, message, group):
        # Sends message to a particular group
        for user in self.getUsersFromGroup(group):
                self.sendMessageToUser(message, user)

    def sendMessageToUser(self, message, user):
        if self.isOnline(user):
        	print 'Found %s online! Sending message' % user
        	self.send(message, user)
        else:
        	print '%s not online. Queueing message' % user
        	self.addMessageToQueue(message, user)

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
        return [user['username'] for user in self.user_info]

    def getUsersFromGroup(self, group_id):
        return [user['username'] for user in self.groups[group_id]]
