import socket
import sys
import select
from chat_client import ChatClient
from functools import wraps
import thread
import Queue
import sys

import rdtp_common

MAX_RECV_LEN = 1024

def timeout(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            response = f(*args, **kwargs)
        except Timeout:
            return 3
        
        return response
    return wrapper

class BadMessageFormat(Exception):
    def __init__(self, message):
        self.message = message
    def __str__(self):
        return "The following message was received from the server in bad format: {}.".format(message)

class Timeout(Exception):
    def __str__(self):
        return "The server timed out."

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
        while 1: # listen forever
            action, status, args = rdtp_common.recv(self.socket)
            if action:
                if action == "R": # Response
                    self.response_queue.put((status, args))
                elif action == "M": # Message
                    message = args[0]
                    sys.stdout.write(message + "\n")
                else:
                    raise BadMessageFormat(message)

    @timeout
    def getNextMessage(self):
        try:
            status, response = self.response_queue.get(block=True, timeout=3)
            return status, response
        except Queue.Empty:
            raise Timeout

    def close(self):
        self.socket.close()

    ##################################
    ### Abstract Method Implementation
    ##################################

    def send(self, action_name, *args):
        rdtp_common.send(self.socket, action_name, 0, *args)

    # request is of type () ->
    def request_handler(self, callback, *args):
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
        Returns boolean."""
        return self.status_request_handler('username_exists', username)

    def create_account(self, username, password):
        """Instructs server to create an account with given username and password."""
        self.send('create_account', username, password)
        status, response = self.getNextMessage()
        if status == 1:
            return False
        return True

    def create_group(self, group_id):
        """Instructs server to create an account with some group_id."""
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
        if status == 1:
            return False
        elif status == 0:
            self.username = username
            self.session_token = response[0]
            return True

    def logout(self):
        """Logout of http-sucks-chat.
        Returns boolean."""
        if not self.session_token:
            return False
        self.send('logout', self.session_token)
        status, response = self.getNextMessage()
        if status == 1:
            return False
        elif status == 0:
            self.username = None
            self.session_token = None
            return True

    def users_online(self):
        """Returns list of users logged into http-sucks-chat."""
        self.send('users_online')
        status, response = self.getNextMessage()
        assert(status == 0)
        return response

    def get_users_in_group(self, group):
        """Returns list of users in some group (including possible wildcard characters)."""
        self.send('get_users_in_group', group)
        status, response = self.getNextMessage()
        assert(status == 0)
        return response

    def send_user(self, user_id, message):
        self.send('send_user', self.session_token, user_id, message)
        status, response = self.getNextMessage()
        if status == 1:
            print "Your session has expired."
        elif status == 2:
            print "Could not send message to " + response[0] + "." 

    def send_group(self, group_id, message):
        self.send('send_group', self.session_token, group_id, message)
        status, response = self.getNextMessage()
        if status == 1:
            print "Your session has expired."
        elif status == 2:
            print "Could not send message to group " + group_id + "."

    def fetch(self):
        """Fetch new messages from the server."""
        self.send('fetch', self.session_token)
        status, response = self.getNextMessage()
        if len(response) == 0 or response[0] == '':
            return "Your inbox is empty."
        else:
            return response[0]
