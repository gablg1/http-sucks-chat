import socket
import select
from pymongo import MongoClient
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

class UserNotLoggedInError(Exception):
    def __init__(self, session_token):
        sefl.username = session_token
    def __str__(self):
        return "User {} is not logged in.".format(session_token)

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

        # Database logic
        client = MongoClient()
        db = client.chat_server
        self.userCollection = db.users
        self.groupCollection = db.groups

    ##################################
    ### For server subclasses
    ##################################

    def username_exists(self, username):
        """Returns user, or None if does not exist."""
        return self.userCollection.find_one({'username' : username})

    def create_account(self, username, password):
        """Create an account with given username and password.
        NOTE: You should check if a username_exists before calling this method."""

        self.userCollection.insert_one(
            {
                'username': username,
                'password': password,
                'groups': [],
                'logged_in': False,
                'session_token': None,
                'messageQ': []
            }
        )
        return True

    def create_group(self, group_name):
        if self.groupCollection.find_one({'name': group_name}):
            raise GroupExists(group_name)

        self.groupCollection.insert_one(
            {
                'name': group_name,
                'users': []
            }
        )

    def login(self, username, password):
        user = self.userCollection.find_one({'username': username})
        if not user:
            return False, ''
        if user['password'] == password:
            if user['logged_in']:
                # Kickout current user, so this guy can log in.
                self.kickout_user(username)
            session_token = ''.join(choice(ascii_uppercase) for i in range(12))
            self.userCollection.update_one(
                {"_id": user["_id"]},
                {
                    "$set": {
                        "logged_in": True,
                        "session_token": session_token
                    }
                }
            )
            return True, session_token
        else:
            return False, ''

    def logout(self, username):
        """Tell MongoDB that a user has been logged out."""
        user = self.userCollection.find_one({'username': username})
        if not user:
            raise UserKeyError(username)

        self.userCollection.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "logged_in": False,
                    "session_token": None
                }
            }
        )

    def users_online(self):
        """Return usernames of users who are logged in."""
        users = self.userCollection.find({"logged_in": True})
        return [user["username"] for user in users]

    def kickout_user(self, username):
        """Kickout the current user. Implementation specific."""

    ##################################
    ### Internal helpers
    ##################################

    def get_users_in_group(self, group_name):
        """Return usernames of users who are in this group."""
        regex = re.compile(group_name)

        # fetch all matching groups
        groups = self.groupCollection.find({"name": regex})

        # create an array of group ids
        group_ids = [group["_id"] for group in groups]

        # fetch all users with that group id
        users = self.userCollection.find({"groups._id": {"$in": group_ids} })

        # generate usernames
        usernames = [user["username"] for user in users]
        return usernames

    def add_user_to_group(self, username, group_name):
        group = self.groupCollection.find_one({'name': group_name})
        if not group:
            raise GroupDoesNotExist(group_name)

        user = self.userCollection.find_one({"username": username})
        if not user:
            raise UserKeyError(username)

        if group_name not in user['groups']:
            self.userCollection.update_one(
                {"_id": user["_id"]},
                {
                    "$push": {
                        "groups": group["_id"]
                    }
                }
            )

            self.groupCollection.update_one(
                {"_id": group["_id"]},
                {
                    "$push": {
                        "users": user["_id"]
                    }
                })

    def send_message_to_group(self, message, group_name):
        """Send message a group with this group_name."""
        group = self.groupCollection.find_one({'name': group_name})
        if not group:
            raise GroupDoesNotExist(group_name)

        for user_id in group['users']:
            user = self.userCollection.find_one({'_id': user_id})
            if user:
                self.send_message_to_user(message, user["username"])
            else:
                print "Tried sending message to non-existant user with id {0} in group {1}.".format(user_id, group_name)

    def send_or_queue_message(self, message, username):
        """send message to a user with this username."""
        user = self.userCollection.find_one({'username': username})
        if not user:
            raise UserKeyError(username)

        if self.is_online(username):
            print 'Found {} online! Sending message.'.format(username)
            self.send_user(message, username)
        else:
            print '{} not online. Queuening message.'.format(username)
            self.userCollection.update_one(
                {"_id": user["_id"]},
                {
                    "$push": {
                        "messageQ": message
                    }
                }
            )

    def is_online(self, username):
        """Check if a user is online. 
        Should be overriden in some server implementations if "logged in"
        scheme is senseless."""
        user = self.userCollection.find_one({'username': username})
        if not user:
            raise UserKeyError(username)

        return user['logged_in'] 

    def get_user_queued_messages(self, username):
        """Get all messages queued for some user."""
        user = self.userCollection.find_one({'username': username})
        if not user:
            raise UserKeyError(username)

        return user["messageQ"]

    def clear_user_message_queue(self, username):
        """Clear all messages queued for some user."""
        user = self.userCollection.find_one({'username': username})
        if not user:
            raise UserKeyError(username)

        self.userCollection.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "messageQ": []
                }
            }
        )

    def get_users(self, query):
        """Return all users who match some regex query."""
        regex = re.compile(query)
        users = self.userCollection.find({"username": regex})
        return [user['username'] for user in users]

    def username_for_session_token(self, session_token):
        user = self.userCollection.find_one({'session_token': session_token})
        if not user:
            raise UserNotLoggedInError(session_token)
        return user['username']
