import socket
import sys
import select
from chat_client import ChatClient
import thread
from Queue import Queue
import sys

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
        self.messageQ = Queue()

    ##################################
    ### Connectivity
    ##################################

    def connect(self):
        self.socket.connect((self.host, self.port))

        # fork thread that will print received messages
        thread.start_new_thread(self.listener, ())

    def listener(self):
        while 1: # listen forever
            message = self.internal_recv(MAX_RECV_LEN)
            if message:
                if message[0] == "C": # Command
                    self.messageQ.put(message[1:])
                elif message[0] == "M": # Message
                    sys.stdout.write("\nNEW MESSAGE RECEIVED: " + message[1:] + "\n> ")
                else:
                    raise BadMessageFormat(message)

    def recv(self):
        while 1: # block until we recieve something on the messageQ
            if not self.messageQ.empty():
                return self.messageQ.get()

    def internal_recv(self, max_len):
        ready_to_read,_,_ = select.select([self.socket],[],[])
        if ready_to_read == []:
            return None
        return self.socket.recv(max_len)

    def send(self, message):
        self.socket.sendall(message)

    def send_action(self, action, *args):
        message = action + ':' + ':'.join(args)
        self.send(message)

    def close(self):
        self.socket.close()

    ##################################
    ### Abstract Method Implementation
    ##################################

    def username_exists(self, username):
        """Check if username already exists.
        Returns boolean."""
        self.send('username_exists:' + username)
        response = self.recv()
        if response == "1":
            return True
        else:
            return False

    def create_account(self, username, password):
        """Instructs server to create an account with given username and password."""
        self.send('create_account:' + username + ':' + password)

    def create_group(self, group_id):
        """Instructs server to create an account with some group_id."""
        self.send_action('create_group', group_id)
        response = self.recv()
        if response == "0":
            print "Group {} already exists.".format(group_id)

    def add_user_to_group(self, username, group_id):
        """Instructs server to add a user to a group."""
        self.send_action('add_to_group', username, group_id)
        response = self.recv()
        if response != "1":
            print "Could not add user to that group."

    def login(self, username, password):
        """Login with given username and password.
        Returns boolean."""
        # First logout of current account
        if self.session_token:
            self.logout

        # Login with new account
        self.send('login:' + username + ':' + password)
        response = self.recv()
        if response == "0":
            return False
        else:
            self.username = username
            self.session_token = response
            return True

    def logout(self):
        """Logout of http-sucks-chat.
        Returns boolean."""
        if not self.session_token:
            return False
        self.send_action('logout', self.session_token)
        response = self.recv()
        if response == "0":
            return False
        else:
            self.username = None
            self.session_token = None
            return True

    def users_online(self):
        """Returns list of users logged into http-sucks-chat."""
        self.send('users_online:')
        response = self.recv()
        if response == "0":
            return []
        return response.split(':')

    def get_users_in_group(self, group):
        """Returns list of users in some group (including possible wildcard characters).""" 
        self.send_action('get_users_in_group', group)
        response = self.recv()
        if response == '0':
            return []
        return response.split(':')

    def send_user(self, user_id, message):
        self.send_action('send_user', self.session_token, user_id, message)
        response = self.recv()
        if response == "0":
            print "Your session has expired."
        elif response == "2":
            print "Could not send message to " + user_id + "."

    def send_group(self, group_id, message):
        self.send_action('send_group', self.session_token, group_id, message)
        response = self.recv()
        if response == "0":
            print "Your session has expired."
        elif response == "1":
            print "Could not send message to group " + group_id + "."

    def fetch(self):
        """Fetch new messages from the server."""
        self.send_action('fetch', self.session_token)
        return self.recv()

    def sendToGroup(self, group_id, message):
        try:
            self.send('send:' + group_id + ':' + message)
        except:
            print "Couldn't send message. Assuming server disconnected."
            self.close()
