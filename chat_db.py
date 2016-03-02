import socket
import select
from pymongo import MongoClient
from random import choice
from string import ascii_uppercase
import re

class GroupKeyError(Exception):
    def __init__(self, group_id):
        self.group_id = group_id
    def __str__(self):
        return "Group {} does not exist.".format(self.group_id)

class UserKeyError(Exception):
    def __init__(self, user_id):
        self.user_id = user_id
    def __str__(self):
        return "User {} does not exist.".format(self.user_id)

class UsernameExists(Exception):
    def __init__(self, username):
        self.username = username
    def __str__(self):
        return "User {} already exists.".format(self.username)

class UsernameDoesNotExist(Exception):
    def __init__(self, username):
        self.username = username
    def __str__(self):
        return "User {} does not exist.".format(self.username)

class UserNotLoggedInError(Exception):
    def __init__(self, session_token):
        self.session_token = session_token
    def __str__(self):
        return "User with session_token {} is not logged in.".format(self.session_token)

class GroupExists(Exception):
    def __init__(self, group_id):
        self.group_id = group_id
    def __str__(self):
        return "Group {} already exists.".format(self.group_id)

class GroupDoesNotExist(Exception):
    def __init__(self, group_id):
        self.group_id = group_id
    def __str__(self):
        return "Group {} does not exist.".format(self.group_id)

class ChatDB(object):
    def __init__(self):
        client = MongoClient()
        db = client.chat_server
        self.userCollection = db.users
        self.groupCollection = db.groups

    def create_account(self, username, password):
        """Create an account with given username and password.
        NOTE: You should check if a username_exists before calling this method."""
        user = self.userCollection.find_one({"username": username})

        if user is not None:
            raise UsernameExists(username)

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

    def login(self, username, password, kickout_method = None):
        user = self.userCollection.find_one({'username': username})
        if user is None:
            return False, ''
        if user['password'] == password:
            if user['logged_in'] and kickout_method:
                # Kickout current user, so this guy can log in.
                kickout_method(username)

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

    def user_exists(self, username):
        user = self.userCollection.find_one({'username': username})
        if user is None:
            return False
        return True

    def needs_kickout(self, username, password):
        user = self.userCollection.find_one({'username': username})
        if user['password'] == password and user['logged_in']:
            return True
        else:
            return False

    def logout(self, username):
        """Tell MongoDB that a user has been logged out."""
        user = self.userCollection.find_one({'username': username})
        if user is None:
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
        print group_ids
        users = self.userCollection.find({"groups": {"$in": group_ids} })

        # generate usernames
        usernames = [user["username"] for user in users]
        return usernames

    def add_user_to_group(self, username, group_name):
        group = self.groupCollection.find_one({'name': group_name})
        if group is None:
            raise GroupDoesNotExist(group_name)

        user = self.userCollection.find_one({"username": username})
        if user is None:
            raise UsernameDoesNotExist(username)

        users_in_group = self.get_users_in_group(group_name)
        if username in users_in_group:
            return

        if group["_id"] not in user['groups']:
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

    def queue_message(self, message, from_username, username):
        user = self.userCollection.find_one({'username': username})
        if user is None:
            raise UserKeyError(username)

        self.userCollection.update_one(
            {"_id": user["_id"]},
            {
                "$push": {
                    "messageQ": {
                        "message": message,
                        "from_username": from_username
                    }
                }
            }
        )

    def is_online(self, username):
        """Check if a user is online. 
        Should be overriden in some server implementations if "logged in"
        scheme is senseless."""
        user = self.userCollection.find_one({'username': username})
        if user is None:
            raise UserKeyError(username)

        return user['logged_in'] 

    def get_user_queued_messages(self, username):
        """Get all messages queued for some user."""
        user = self.userCollection.find_one({'username': username})
        if not user:
            raise UserKeyError(username)

        return user['messageQ']

    def clear_user_message_queue(self, username):
        """Clear all messages queued for some user."""
        user = self.userCollection.find_one({'username': username})
        if user is None:
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
        return list(users)

    def get_groups(self, query):
        """Return all groups who match some regex query."""
        regex = re.compile(query)
        groups = self.groupCollection.find({"name": regex})
        return list(groups)

    def delete_account(self, username):
        """Deletes the account corresponding to a username."""
        self.userCollection.remove({"username": username})

    def username_for_session_token(self, session_token):
        user = self.userCollection.find_one({'session_token': session_token})
        if user is None:
            raise UserNotLoggedInError(session_token)
        return user['username']

    def get_users(self, query):
        """Return all users who match some regex query."""
        regex = re.compile(query)
        users = self.userCollection.find({"username": regex})
        return list(users)

    def get_groups(self, query):
        """Return all groups who match some regex query."""
        regex = re.compile(query)
        groups = self.groupCollection.find({"name": regex})
        return list(groups)
