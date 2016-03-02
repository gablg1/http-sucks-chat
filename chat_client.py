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
        if len(params.split()) != 2:
            print "The appropriate command format is: register [username] [password]"
        else:
            username, password = params.split()
            if not self.create_account(username, password):
                print "Username {} already exists.".format(username)

            print "User {} created.".format(username)

    def do_create_group(self, group_id):
        """create_group [group]
        Creates a new group."""
        response = self.create_group(group_id)
        if response == 1:
            print "Your session has expired."
        elif response == 2:
            print "Group {} already exists.".format(group_id)
        elif response == 3:
            print "Server timed out. Are you connected?"

        print "Group {} created.".format(group_id)


    def do_add_user_to_group(self, params):
        """add_user_to_group [username] [group]
        Adds a user to a specified group."""
        if len(params.split()) != 2:
            print "The appropriate command format is: add_user_to_group [username] [group]"
        else:
            username, group_id = params.split()
            status = self.add_user_to_group(username, group_id)
            if status == 1:
                print "Your session has expired."
            elif status == 2:
                print "Could not add user {} to group {}. Please, try again.".format(username, group_id)
            elif status == 3:
                print "Server timed out. Are you connected?"

            print "User {} added to group {} successfully.".format(username, group_id)

    def do_login(self, params):
        """login [username] [password]
        Login to http-sucks-chat."""
        if len(params.split()) != 2:
            print "The appropriate command format is: login [username] [password]."
        elif self.loggedIn:
            print "You are already logged into http-sucks-chat."
        else:
            username, password = params.split()
            if self.login(username, password):
                self.loggedIn = True
                self.username = username
                print "Logged in."
            else:
                print "Could not log into http-sucks-chat with that username and password."

    def do_logout(self, _):
        """logout
        Logout of http-sucks-chat."""
        if self.logout():
            self.loggedIn = False
            print "Logged out."
        else:
            print "Could not log out of http-sucks-chat."

    def do_users_online(self, _):
        """users_online
        Get list of users logged in to http-sucks-chat."""
        users = self.users_online()
        if len(users) == 0:
            print "No users are logged in."
        else:
            print 'There are {0} users logged in: {1}'.format(len(users), ','.join(users))

    def do_users_in_group(self, group):
        """users_in_group [group]
        Get a list of users in some group."""
        users = self.get_users_in_group(group)
        if len(users) == 0:
            print "No users in group " + group + "."
        else:
            print "Users in group {0}: {1}.".format(group, ', '.join(users))

    ##################################
    ### User Interaction
    ##################################

    @check_authorization
    def do_send(self, body):
        """Send a message to a user of your choice."""
        if len(body.split(' ', 1)) != 2:
            print "Usage: send_user [user] [message]"
        else:
            user_id, message = body.split(' ', 1)
            status = self.send_user(user_id, message)
            if status == 1:
                print "Your session has expired."
            elif status == 2:
                print "Could not send message to " + user_id + "."
            elif status == 3:
                print "Server timed out. Are you connected?"

    @check_authorization
    def do_send_group(self, body):
        """Send a message to a group of your choice."""
        if len(body.split(' ', 1)) != 2:
            print "Usage: send_group [group] [message]"
        else:
            group_id, message = body.split(' ', 1)
            status = self.send_group(group_id, message)
            if status == 1:
                print "Your session has expired."
            elif status == 2:
                print "Could not send message to group " + group_id + "."
            elif status == 3:
                print "Server timed out. Are you connected?"

    @check_authorization
    def do_fetch(self, _):
        """Fetch new messages from the server.
        You must be logged in to use this command."""
        response = self.fetch()
        if response == 1:
            print "Your session has expired."
        elif response == 2:
            print "Could not fetch messages. Please, try again."
        elif response == 3:
            print "Server timed out. Are you connected?"

        print response

    @check_authorization
    def do_join_group(self, group_id):
        """join_group [group]
        Join a group. Must be logged in.
        You must be logged in to use this command."""
        status = self.add_user_to_group(self.username, group_id)
        if status == 1:
            print "Your session has expired."
        elif status == 2:
            print "Could not add you to group {}. Please, try again.".format(group_id)
        elif status == 3:
            print "Server timed out. Are you connected?"

        print "You were added to group {} successfully.".format(group_id)

    @check_authorization
    def do_get_groups(self, wildcard='.*'):
        """get_groups [query]
        Returns a list of groups matching your query. You can use a wildcard!
        You must be logged in to use this command."""
        response = self.get_groups(wildcard)
        if response == 1:
            print "Your session has expired."
        elif response == 2:
            print "Could not get groups. Please, try again."
        elif response == 3:
            print "Server timed out. Are you connected?"

        print "These groups match your query:"
        print response

    @check_authorization
    def do_get_users(self, wildcard='.*'):
        """get_groups [query]
        Returns a list of groups matching your query. You can use a wildcard!
        You must be logged in to use this command."""
        response = self.get_users(wildcard)
        if response == 1:
            print "Your session has expired."
        elif response == 2:
            print "Could not get users. Please, try again."
        elif response == 3:
            print "Server timed out. Are you connected?"

        print "These users match your query:"
        print response

    @check_authorization
    def do_delete_account(self, _):
        """delete_account
        Delete your account.
        You must be logged in to use this command.
        """
        status = self.delete_account()
        if status == 1:
            print "Your session has expired."
        elif status == 2:
            print "Could not delete your account. Please, try again."
        elif status == 3:
                print "Server timed out. Are you connected?"
        self.loggedIn = False

        print "Account deleted successfully."

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
    def get_users_in_group(self, group):
        """Returns list of users in some group (including possible wildcard characters).""" 

    @abstractmethod
    def get_groups(self, wildcard):
        """Returns all groups."""

    @abstractmethod
    def get_users(self, wildcard):
        """Returns all users."""

    @abstractmethod
    def send_user(self, user_id, message):
        """Send a message to the user."""

    @abstractmethod
    def send_group(self, group_id, message):
        """Send a message to the group."""

    @abstractmethod
    def fetch(self):
        """Fetch new messages from the server."""
