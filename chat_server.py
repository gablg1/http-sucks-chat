import socket
import select
from sets import Set
from random import choice
from string import ascii_uppercase
import re

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

class ChatServer(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        # assuming 3 users here, who cares
        self.amazing_queue = {} # lookup by username. Each will be a list.
        self.user_info = {} # lookup by username. Each will be a user_info dictionary.
        self.groups = {} # lookup by group id. Each will be a list
        self.logged_in_users = {} # lookup by session token. Each will be a user_info dictionary.

    ##################################
    ### For server subclasses
    ##################################

    def username_exists(self, username):
        return username in self.amazing_queue

    def create_account(self, username, password, group_id = None):
        # !# THIS NEEDS TO CHECK IF USERNAME IS TAKEN

        self.amazing_queue[username] = []
        self.user_info[username] = {
            'username': username,
            'password': password,
            'group_id': [group_id],
            'logged_in': False,
            'session_token': None
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
            print group_id
            self.groups[group_id] = []

    def login(self, username, password):
        if username not in self.user_info:
            return False, ''
        user = self.user_info[username]
        if user['password'] == password:
            if self.user_info[username]['logged_in']:
                # Kickout current user, so this guy can log in.
                self.kickout_user(username)
            user['logged_in'] = True
            user['session_token'] = ''.join(choice(ascii_uppercase) for i in range(12))
            self.logged_in_users[user['session_token']] = user
            return True, user['session_token']
        else:
            return False, ''

    def users_online(self):
        return [self.logged_in_users[user]['username'] for user in self.logged_in_users]

    def kickout_user(self, username):
        """Kickout the current user."""

    ##################################
    ### Internal helpers
    ##################################

    def get_users_in_group(self, group):
        regex = re.compile(group)
        group_names = [key for key in self.groups if re.match(regex, key)]
        groups = [self.groups[group_name] for group_name in group_names] # list of list of users
        usernames = [val["username"] for sublist in groups for val in sublist]
        return usernames

    def add_user_to_group(self, username, group_id):
        if group_id not in self.groups:
            raise GroupDoesNotExist(group_id)
        
        user = self.user_info[username]
        if group_id not in user['group_id']:
            self.groups[group_id].append(user)
            user['group_id'].append(group_id)

    def send_message_to_group(self, message, group):
        # !# THIS NEEDS TO CHECK IF GROUP EXISTS
        for user in self.get_users_from_group(group):
            self.send_message_to_user(message, user)

    def send_message_to_user(self, message, user):
        # !# THIS NEEDS TO CHECK IF USER EXISTS
        if self.is_online(user):
        	print 'Found %s online! Sending message' % user
        	self.send(message, user)
        else:
        	print '%s not online. Queueing message' % user
        	self.add_message_to_queue(message, user)

    def add_message_to_queue(self, message, user):
        # !# THIS NEEDS TO CHECK IF USER EXISTS
        self.amazing_queue[user].append(message)

    def get_user_queued_messages(self, user):
        # !# THIS NEEDS TO CHECK IF USER EXISTS
        return self.amazing_queue[user]

    # Moved self.isOnline to inside rdtp and http servers
    # in http, we don't want anyone online (at least as of now)

    def get_users(self):
        return [user['username'] for user in self.user_info]

    def get_users_from_group(self, group_id):
        # !# THIS NEEDS TO CHECK IF GROUP EXISTS
        return [user['username'] for user in self.groups[group_id]]
