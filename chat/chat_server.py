from chat_db import ChatDB
from chat_db import UsernameExists

class ChatServer(object):
    """
    Implements the interface of the different operations performed by the
    server. Notice that the functions here are almost always simple wrappers
    to functions in ChatDB. Those may raise exceptions, and should be handled
    appropriately by the caller; this class does NOT handle them.
    """
    
    def __init__(self, host, port):
        """
        Initializes a ChatServer host and port class variables.
        Also starts the ChatDB instance, which handles interactions 
        with an underlying database. 

        :param host: The host where this client should connect to
        :param port: The port that this client should connect to
        """
        self.host = host
        self.port = port
        self.chatDB = ChatDB()

    def kickout_user(self, username):
        """
        Kickout the current user. Implementation specific.
        """

    def create_account(self, username, password):
        """
        Create an account with given username and password.

        :param username: The username of the account to be created
        :param password: The corresponding password
        """
        self.chatDB.create_account(username, password)

    def login(self, username, password):
        """
        Login to an account with given username and password.

        :param username: The username of the account to be logged in
        :param password: The corresponding password
        """
        self.chatDB.login(username, password, self.kickout_user)

    def logout(self, username):
        """
        Logout off an account given a username.

        :param username: The username of the account to be logged off
        """
        self.chatDB.logout(username)

    def is_online(self, username):
        """
        Check if a user is online. 

        Should be overriden in some server implementations if "logged in"
        scheme is senseless.

        :param username: Username that we want to check

        :return: True if user is online, False otherwise
        """
        return self.chatDB.is_online(username)

    def delete_account(self, username):
        """
        Deletes the account corresponding to a username.

        :param username: Username to be deleted
        """
        self.chatDB.delete_account(username)

    def username_for_session_token(self, session_token):
        """
        Fetches a username, given a session token.

        :param session_token: The session token to be queried

        :return: The username matching the session_token.
        """

        return self.chatDB.username_for_session_token(session_token)

    ###########
    ## GROUP ##
    ###########

    def create_group(self, group_name):
        return self.chatDB.create_group(group_name)

    def get_users(self, query):
        """
        Return all users who match some regex query.

        :param query: The regex query to be matched

        :return: List of matching users
        """
        return self.chatDB.get_users(query)

    def add_user_to_group(self, username, group_name):
        """
        Adds a user to a group.

        :param username: The username to be added
        :param group_name: The group to which the user should be added
        """
        
        self.chatDB.add_user_to_group(username, group_name)

    def get_groups(self, query):
        """
        Return all groups that match some regex query.

        :param query: The regex query to be matched

        :return: List of matching groups
        """

        return self.chatDB.get_groups(query)

    #############
    ## MESSAGE ##
    #############

    def send_message_to_group(self, session_token, message, group_name):
        """
        Send message to a group with this group_name. This uses send_or_queue_message
        in a loop.

        :param session_token: The session_token of the sender.
        :param message: The message to be sent.
        :param group_name: The group to which message will be sent.
        """
        users = self.chatDB.get_users_in_group(group_name)

        for username in users:
            self.send_or_queue_message(session_token, message, username, group_name)

    def send_or_queue_message(self, session_token, message, username, group_name = None):
        """
        Send message to a user (or queue it, if user is not online).

        :param session_token: The session_token of the sender.
        :param message: The message to be sent.
        :param username: The user to which the message is sent.
        :param group_name: The group where this message was sent; default is None 
        """

        from_username = self.chatDB.username_for_session_token(session_token)

        if self.is_online(username):
            try:
                self.send_user(message, from_username, username, group_name)
                print 'Found {} online! Sending message.'.format(username)
            except:
                self.chatDB.queue_message(message, from_username, username, group_name)
                print '{} not online. Queuening message.'.format(username)
        else:
            self.chatDB.queue_message(message, from_username, username, group_name)
            print '{} not online. Queuening message.'.format(username)

    def get_user_queued_messages(self, username):
        """
        Get all messages queued for some user.

        :param username: Username for which to get queued messages.

        :return: List of all queued messages.
        """
        return self.chatDB.get_user_queued_messages(username)

    def clear_user_message_queue(self, username):
        """
        Clear all messages queued for some user.

        :param username: Username for which to clear.
        """
        self.chatDB.clear_user_message_queue(username)
