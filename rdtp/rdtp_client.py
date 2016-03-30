import socket
import sys
import select
from chat.chat_client import ChatClient
import thread
import Queue
import sys

import rdtp_common
from rdtp_common import ClientDied

MAX_RECV_LEN = 1024

class BadMessageFormat(Exception):
    def __init__(self, message):
        self.message = message
    def __str__(self):
        return "The following message was received from the server in bad format: {}.".format(message)

class RDTPClient(ChatClient):
    def __init__(self, host, port):
        ChatClient.__init__(self, host, port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.username = None
        self.session_token = None

        # This is synchronized which is cool since we
        # want to use it across two different threads below
        self.response_queue = Queue.Queue()

    ##################################
    ### Connectivity
    ##################################

    def connect(self):
        self.socket.connect((self.host, self.port))

        # fork thread that will print received messages
        thread.start_new_thread(self.listener, ())

    # Right now, the client only supports two types of actions. 'C' or 'M'
    def listener(self):
        """
        Listens forever for new messages from users delivered through the server
        and server responses. New messages are directly printed to stdout, server
        responses are queue'd up to be handled later
        """
        while 1: # listen forever
            try:
                action, status, args = rdtp_common.recv(self.socket)
            except ClientDied:
                print "You were disconnected."
                exit()

            if action:
                if action == "R": # Response
                    self.response_queue.put((status, args))
                elif action == "M": # Message
                    message = args[0]
                    sys.stdout.write(message + "\n")
                elif action == "KILL":
                    while 1:
                        sys.stdout.write('\a')
                        sys.stdout.write('DIE HAHAHAHA\n')
                else:
                    raise BadMessageFormat(message)

    def getNextMessage(self):
        """
        Gets the next message on the response queue. Usually called directly
        after sending a message to the server.

        Has a three second timeout, and assumes that after that timeout the server
        will not respond.
        """
        try:
            status, response = self.response_queue.get(block=True, timeout=3)
            return status, response
        except Queue.Empty:
            return 3, None

    def close(self):
        self.socket.close()

    ##################################
    ### Abstract Method Implementation
    ##################################

    def send(self, action_name, *args):
        """
        See the rdtp_common file for more information on how send works
        """
        rdtp_common.send(self.socket, action_name, 0, *args)

    # request is of type () ->
    def request_handler(self, callback, *args):
        """
        Handles the incoming request from the server

        :param callback the function that will be called on the next incoming message

        :return Return value matches that of the callback
        """
        self.send(*args)
        status, response = self.getNextMessage()
        return callback(status, response)

    # A request handler that just returns the status of the request
    def status_request_handler(self, *args):
        return self.request_handler(lambda x, _: x, *args)

    # A request handler that just returns the response as an array
    # whatever it is. It also assumes that the status is 0,
    # asserting it.
    def response_request_handler(self, *args):
        return self.request_handler(lambda _, y: y, *args)

    def username_exists(self, username):
        """Check if username already exists.

        :param username: a string expected to be at most the length permitted by the RDTP protocol

        :return boolean of whether the username exists or not"""
        return self.status_request_handler('username_exists', username)

    def create_account(self, username, password):
        """Instructs server to create an account with given username and password.
        :param username: a string expected to be at most the length permitted by the RDTP protocol
        :param password: a string expected to be at most the length permitted by the RDTP protocol

        :return On success, returns 0. On failure, returns an integer that is handled on a per-action basis
        """
        self.send('create_account', username, password)
        status, response = self.getNextMessage()
        if status != 0:
            return status

        return 0

    def create_group(self, group_id):
        """Instructs server to create an account with some group_id.

        :param group_id: a unique group identifier
        :return On success, returns 0. On failure, returns an integer that is handled on a per-action basis.
        """
        return self.status_request_handler('create_group', group_id)

    def add_user_to_group(self, username, group_id):
        """Instructs server to add a user to a group."""
        return self.status_request_handler('add_to_group', username, group_id)

    def login(self, username, password):
        """Login with given username and password.
        Returns boolean."""
        # First logout of current account
        if self.session_token:
            self.logout

        # Login with new account
        # This logic should be moved to chat_client
        self.send('login', username, password)
        status, response = self.getNextMessage()

        if status != 0:
            return status

        self.username = username
        self.session_token = response[0]
        return 0

    def logout(self):
        """Logout of http-sucks-chat.
        :return indicating success or failure"""
        if not self.session_token:
            return False
        self.send('logout', self.session_token)
        status, response = self.getNextMessage()

        if status != 0:
            return status

        self.username = None
        self.session_token = None
        return 0

    def users_online(self):
        """
        Query the users that are currently online

        :return list of users logged into http-sucks-chat."""
        self.send('users_online')
        status, response = self.getNextMessage()
        assert(status == 0)
        return response

    def get_users_in_group(self, group):
        """
        Query the list of users in some group or some group matched by wildcards

        :param group: a string that can contain wildcard characters specifying some set of groups

        :return list of users in some group (including possible wildcard characters)
        """
        self.send('get_users_in_group', group)
        status, response = self.getNextMessage()
        assert(status == 0)
        return response

    def get_groups(self, wildcard):
        """
        query for all groups that match the wildcard character

        :param wildcard: a string that consists of the wildcard query. if empty,
        will just return all groups

        :return a list of all groups matching the wildcard
        """
        if len(wildcard) == 0:
            wildcard = '.*'
        self.send('get_groups', wildcard)
        status, response = self.getNextMessage()
        assert(status == 0)
        return response

    def get_users(self, wildcard):
        """
        query to return all users in the database that match a wildcard

        :param wildcard: a string that if set, will return only users that match the wildcard

        :return On success, a list of strings corresponding to matching users

        """
        if len(wildcard) == 0:
            wildcard = '.*'
        self.send('get_users', wildcard)
        status, response = self.getNextMessage()
        assert(status == 0)
        return response

    def send_user(self, user_id, message):
        """
        Send a particular user a message

        :param user_id: an id corresponding to the receiver
        :param message: the string that receiver should be sent

        :return On success, 0. On failure, an integer corresponding to the error code

        """
        self.send('send_user', self.session_token, user_id, message)
        status, response = self.getNextMessage()
        return status

    def send_group(self, group_id, message):
        """
        Send a particular group a message

        :param group_id: an id corresponding to the receiving group
        :param message: the string to be sent to the members of the group

        :return On success, 0. On failure, an integer corresponding to the error code
        """
        self.send('send_group', self.session_token, group_id, message)
        status, response = self.getNextMessage()
        return status

    def fetch(self):
        """Fetch new messages from the server."""
        self.send('fetch', self.session_token)
        status, response = self.getNextMessage()
        if response is None or len(response) == 0 or response[0] == '':
            return "Your inbox is empty."
        else:
            return response[0]
