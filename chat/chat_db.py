import socket
import select
from pymongo import MongoClient
from random import choice
from string import ascii_uppercase
import re

################
## EXCEPTIONS ##
################

class GroupKeyError(Exception):
    """
    Exception subclass, raised during attempted use of non-existent groups.
    """
    def __init__(self, group_id):
        self.group_id = group_id
    def __str__(self):
        return "Group {} does not exist.".format(self.group_id)

class UserKeyError(Exception):
    """
    Exception subclass, raised during attempted use of non-existent users.
    """
    def __init__(self, user_id):
        self.user_id = user_id
    def __str__(self):
        return "User {} does not exist.".format(self.user_id)

class UsernameExists(Exception):
    """
    Exception subclass, raised when a user is trying to be created, but already exists.
    """
    def __init__(self, username):
        self.username = username
    def __str__(self):
        return "User {} already exists.".format(self.username)

class UsernameDoesNotExist(Exception):
    """
    Exception subclass, raised when a user is trying to be used, but does not exist.
    """
    def __init__(self, username):
        self.username = username
    def __str__(self):
        return "User {} does not exist.".format(self.username)

class UserNotLoggedInError(Exception):
    """
    Exception subclass, raised when a user needs to be logged in for some action, but is not logged in.
    """
    def __init__(self, session_token):
        self.session_token = session_token
    def __str__(self):
        return "User with session_token {} is not logged in.".format(self.session_token)

class GroupExists(Exception):
    """
    Exception subclass, raised when a group is trying to be created, but already exists.
    """
    def __init__(self, group_id):
        self.group_id = group_id
    def __str__(self):
        return "Group {} already exists.".format(self.group_id)

class GroupDoesNotExist(Exception):
    """
    Exception subclass, raised when a group needs to exist for some action, but does not already exist.
    """
    def __init__(self, group_id):
        self.group_id = group_id
    def __str__(self):
        return "Group {} does not exist.".format(self.group_id)

################
## DB MANAGER ##
################

class ChatDB(object):
    """
    Handles all database related actions for the application.
    Anything that involves persistance across application launches is
    incorporated into this class.

    Server subclasses will call into ChatDB in order to complete their actions.
    Therefore, the application workflow is:
        client -> server -> chat_db -> server -> client
    """

    def __init__(self):
        """
        Initializes a ChatDB on the given host and port.
        Sets up the underlying MongoClient that is used
        for all database-related tasks.
        """
        client = MongoClient()
        db = client.chat_server
        self.userCollection = db.users
        self.groupCollection = db.groups

    ##########
    ## USER ##
    ##########

    def create_account(self, username, password):
        """
        Create an account with given username and password.
        NOTE: You should check if a username_exists before calling this method.

        :param username: The username for the new account.
        :param password: The password for the new account.
        """

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

    def login(self, username, password, kickout_method = None):
        """
        Login to some account, with a given username and password.
        A function, kickout_method, can be provided. If provided,
        the function is called on this username, to kickout an
        already logged in user. kickout_method exists as this
        logic is required for any chat application that cannot have
        multiple people using the same account at the same time.

        :param username: The username for logging in.
        :param password: The password for logging in.
        :param kickout_method: Defaults to None.
                               The kickout_method to be applied to username if a user is already logged in on this account.
        :return: tuple of (False, '') on failure, tuple of (True, session_token) on success.
        """

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
        """
        Check if a user already exists with some username.

        :param username: The username to check for existance.
        :return: True if user exists. False if no user exists with this username.
        """

        user = self.userCollection.find_one({'username': username})
        if user is None:
            return False
        return True

    def is_online(self, username):
        """
        Check if a user is online.
        Should be overriden in some server implementations if "logged in"
        scheme is senseless.

        Requires the username to already exist.

        :param username: The username to check if is online.
        :return: True is user is online. False if user is not online.
        :raises: UserKeyError if no user exists with this username.
        """

        user = self.userCollection.find_one({'username': username})
        if user is None:
            raise UserKeyError(username)

        return user['logged_in']

    def needs_kickout(self, username, password):
        """
        Determine whether a user needs to be kicked out.
        If the username and password match, and the user is logged_in, will return True.
        Otherwise, returns False.

        :param username: The username to check.
        :param password: The password to check.
        :return: True if the username and password match, and the user is logged_in.
                 False otherwise.
        """

        user = self.userCollection.find_one({'username': username})
        if user['password'] == password and user['logged_in']:
            return True
        else:
            return False

    def logout(self, username):
        """
        Tell the underlying database (MongoDB) that a user has been logged out.

        :param username: The username to logout.
        """

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
        """
        Returns list of usernames of users who are logged in.

        :return: List of usernames of users who are logged in.
        """

        users = self.userCollection.find({"logged_in": True})
        return [user["username"] for user in users]

    def delete_account(self, username):
        """
        Deletes the account corresponding to a username.

        :param username: The username of the account to delete.
        """
        self.userCollection.remove({"username": username})

    def username_for_session_token(self, session_token):
        """
        Get username associated with some session token.
        Requires that a user be logged in with this session_token to complete.

        :param session_token: The session_token to lookup.
        :return: The username of the user logged in with this session_token.
        :raises: UserNotLoggedInError if there is no user logged in with this session_token.
        """
        user = self.userCollection.find_one({'session_token': session_token})
        if user is None:
            raise UserNotLoggedInError(session_token)
        return user['username']

    def get_users(self, query):
        """
        Return a list of all users who match some regex query.

        :param query: The regex query to evaluate.
        :return: A list of users who are logged in.
        """
        regex = re.compile(query)
        users = self.userCollection.find({"username": regex})
        return list(users)

    ###########
    ## GROUP ##
    ###########

    def create_group(self, group_name):
        """
        Create a group with some group name.

        :param group_name: The name of the group to create.
        """

        if self.groupCollection.find_one({'name': group_name}):
            raise GroupExists(group_name)

        self.groupCollection.insert_one(
            {
                'name': group_name,
                'users': []
            }
        )

    def get_users_in_group(self, group_name):
        """
        Return the usernames of users who are in some group.

        :param group_name: The name of the group to lookup.
        """

        regex = re.compile(group_name)

        # fetch all matching groups
        groups = self.groupCollection.find({"name": regex})

        # create an array of group ids
        group_ids = [group["_id"] for group in groups]

        if group_ids == []:
            raise GroupDoesNotExist(group_name)

        # fetch all users with that group id
        users = self.userCollection.find({"groups": {"$in": group_ids} })

        # generate usernames
        usernames = [user["username"] for user in users]
        return usernames

    def add_user_to_group(self, username, group_name):
        """
        Add a user to some group.

        :param username: The username of the user to add to this group.
        :param group_name: The name of the group to which to add this user.
        :raises: GroupDoesNotExist if the group does not exist.
                 UsernameDoesNotExist if the username does not exist.
        """

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

    def get_groups(self, query):
        """
        Returns all groups that match some regex query.

        :param query: The query to lookup.
        :return: A list of groups that match the provided regex query.
        """
        regex = re.compile(query)
        groups = self.groupCollection.find({"name": regex})
        return list(groups)

    ##############
    ## MESSAGES ##
    ##############

    def queue_message(self, message, from_username, username, group_name = None):
        """
        Add a message to the queue of some user, for delivery later.

        :param message: The message string to deliver.
        :param from_username: The username of the user who is sending this message.
        :param username: The username of the user to which this message should be delivered.
        :param group_name: If this message is sent as part of a group message, the name of the group from which it is sent (optional).
        :raises: UserKeyError if the user does not exist.
        """

        user = self.userCollection.find_one({'username': username})
        if user is None:
            raise UserKeyError(username)

        self.userCollection.update_one(
            {"_id": user["_id"]},
            {
                "$push": {
                    "messageQ": {
                        "message": message,
                        "from_username": from_username,
                        "from_group_name": group_name
                    }
                }
            }
        )

    def get_user_queued_messages(self, username):
        """
        Get all messages queued for some user.

        :param username: The username to lookup.
        :return: A list of messages in the message queue of this user.
        :raises: UserKeyError if the user does not exist.
        """

        user = self.userCollection.find_one({'username': username})
        if not user:
            raise UserKeyError(username)

        return user['messageQ']

    def clear_user_message_queue(self, username):
        """
        Clear all messages queued for some user.

        :param username: The username of the user whose messages should be cleared.
        :raises: UserKeyError if the user does not exist.
        """
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
