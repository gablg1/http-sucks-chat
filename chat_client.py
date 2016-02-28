from abc import abstractmethod
from functools import wraps
import cmd

def check_authorization(f):
    @wraps(f)
    def wrapper(*args):
        loggedIn = args[0].loggedIn
        if not loggedIn:
            print "Please log in to use that command."
        else:
            return f(*args)
    return wrapper

class ChatClient(cmd.Cmd):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.loggedIn = False

        self.prompt = '> '
        self.intro = 'Welcome to the HTTP Sucks Chat!'

        cmd.Cmd.__init__(self)

    ##################################
    ### Registration
    ##################################

    def do_register(self, params):
        """register [username] [password]
        Create a new account."""
        username, password = params.split()
        if self.username_exists(username):
            print "An account already exists with that username. Please try again."
        else:
            self.create_account(username, password)

    def do_create_group(self, group_id):
        """create_group [group]
        Creates a new group."""
        self.create_group(group_id)

    def do_add_user_to_group(self, params):
        """add_user_to_group [username] [group]
        Adds a user to a specified group."""
        username, group_id = params.split()
        self.add_user_to_group(username, group_id)

    def do_login(self, params):
        """login [username] [password]
        Login to http-sucks-chat."""
        username, password = params.split()
        if self.login(username, password):
            self.loggedIn = True
            self.username = username
        else:
            print "Could not log into http-sucks-chat with that username and password."

    def do_logout(self, params):
        """logout
        Logout of http-sucks-chat."""
        if self.logout():
            self.loggedIn = False
        else:
            print "Could not log out of http-sucks-chat."

    def do_users_online(self, params):
        """users_online
        Get list of users logged in to http-sucks-chat."""
        users = self.users_online()
        if len(users) == 0:
            print "No users are logged in."
        else:
            print 'There are {0} users logged in: {1}'.format(len(users), ','.join(users))

    ##################################
    ### User Interaction
    ##################################

    @check_authorization
    def do_send_user(self, body):
        """Send a message to a user of your choice."""
        user_id, message = body.split(' ', 1)
        self.send_user(user_id, message)

    @check_authorization
    def do_send_group(self, body):
        """Send a message to a group of your choice."""
        group_id, message = body.split(' ', 1)
        self.send_group(group_id, message)

    @check_authorization
    def do_fetch(self, params):
        """Fetch new messages from the server."""
        print self.fetch()

    @check_authorization
    def do_join_group(self, group_id):
        """Join a group. Must be logged in.
        join_group [group]"""
        self.add_user_to_group(self.username, group_id)

    ##################################
    ### Abstract Methods
    ##################################

    @abstractmethod
    def username_exists(self, username):
        """Check if username already exists.
        Returns boolean."""

    @abstractmethod
    def create_account(self, username, password):
        """Instructs server to create an account with given username and password."""

    @abstractmethod
    def create_group(self, group_id):
        """Instructs server to create an account with some group_id."""

    @abstractmethod
    def add_user_to_group(self, username, group_id):
        """Instructs server to add a user to a group."""

    @abstractmethod
    def login(self, username, password):
        """Login with given username and password.
        Returns boolean."""

    @abstractmethod
    def logout(self):
        """Logout of http-sucks-chat.
        Returns boolean."""

    @abstractmethod
    def users_online(self):
        """Returns list of users logged into http-sucks-chat."""

    @abstractmethod
    def send_user(self, user_id, message):
        """Send a message to the user."""

    @abstractmethod
    def send_group(self, group_id, message):
        """Send a message to the group."""

    @abstractmethod
    def fetch(self):
        """Fetch new messages from the server."""
