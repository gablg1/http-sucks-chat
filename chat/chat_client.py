from functools import wraps
import cmd

def check_authorization(f):
    """
    Wrapper that checks if the user is logged in.
    """

    @wraps(f)
    def wrapper(*args):
        loggedIn = args[0].loggedIn
        if not loggedIn:
            print "Please log in to use that command."
        else:
            return f(*args)
    return wrapper

class ChatClient(cmd.Cmd):
    """
    Implements the interface of the different operations performed by the
    client.

    Dependencies: This module inherits from cmd.Cmd, which provides a simple
    yet useful interface for the command line. The methods implemented in this
    class will be called automatically by cmd.Cmd in the method cmd_loop(), 
    which should be called to start this client. The documentation for cmd.Cmd
    can be found here: [https://docs.python.org/2/library/cmd.html]
    """
    
    def __init__(self, host, port):
        """
        Initializes a ChatClient host and port class variables, as well
        as setup some simple configuration for the command line interface
        and set loggedIn to false. Also initializes the command line
        interface (with cmd.Cmd)

        :param host: The host where this client should connect to
        :param port: The port that this client should connect to
        """

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
        """
        Create a new user account.

        :param params: The parameters passed in to the command line interface,
        which have to be broken down into username and password (separated by spaces)
        """

        if len(params.split()) != 2:
            print "The appropriate command format is: register [username] [password]"
        else:
            username, password = params.split()
            status = self.create_account(username, password)
            if status == 2:
                print "Username {} already exists.".format(username)
            elif status == 3:
                print "Server timed out. Are you connected?"
            else:
                print "User {} created.".format(username)

    @check_authorization
    def do_create_group(self, group_id):
        """
        Creates a new group. Assumes user is logged in.

        :param group_id: The group to be created.
        """

        response = self.create_group(group_id)
        if response == 1:
            print "Your session has expired."
        elif response == 2:
            print "Group {} already exists.".format(group_id)
        elif response == 3:
            print "Server timed out. Are you connected?"
        else:
            print "Group {} created.".format(group_id)

    @check_authorization
    def do_add_user_to_group(self, params):
        """
        Adds a user to a specified group. Assumes user is logged in.

        :param params: The parameters passed in to the command line interface,
        which have to be broken down into username and group_id (separated by spaces)
        """

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
            else:
                print "User {} added to group {} successfully.".format(username, group_id)

    def do_login(self, params):
        """
        Login with credentials.

        :param params: The parameters passed in to the command line interface,
        which have to be broken down into username and password (separated by spaces)
        """

        if len(params.split()) != 2:
            print "The appropriate command format is: login [username] [password]."
        elif self.loggedIn:
            print "You are already logged into http-sucks-chat."
        else:
            username, password = params.split()
            status = self.login(username, password)

            if status == 0:
                self.loggedIn = True
                self.username = username
                print "Logged in."
            elif status == 3:
                print "Server timed out. Are you connected?"
            else:
                print "Could not log into http-sucks-chat with that username and password."

    @check_authorization
    def do_logout(self, _):
        """
        Logout from the current session. Assumes user is logged in.

        The parameter is mandatory for cmd.Cmd, but we ignore it.
        """
        status = self.logout()

        if status == 0:
            self.loggedIn = False
            print "Logged out."
        elif status == 3:
            print "Server timed out. Are you connected?"
        else:
            print "Could not log out of http-sucks-chat."

    ##################################
    ### User Interaction
    ##################################

    @check_authorization
    def do_send(self, params):
        """
        Send a message to a specific user. Assumes user is logged in.

        :param params: The parameters passed in to the command line interface,
        which have to be broken down into user_id and message. The first word
        (separated by spaces) will be considered the user; all the rest will be
        considered part of the message and will be sent.
        """

        if len(params.split(' ', 1)) != 2:
            print "Usage: send_user [user] [message]"
        else:
            user_id, message = params.split(' ', 1)
            status = self.send_user(user_id, message)
            if status == 1:
                print "Your session has expired."
            elif status == 2:
                print "Could not send message to user " + user_id + "."
            elif status == 3:
                print "Server timed out. Are you connected?"

    @check_authorization
    def do_send_group(self, body):
        """
        Send a message to a specific group. Assumes user is logged in.

        :param params: The parameters passed in to the command line interface,
        which have to be broken down into group_id and message. The first word
        (separated by spaces) will be considered the group; all the rest will be
        considered part of the message and will be sent.
        """

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
        """
        Fetch (and print) messages for currently logged in user. Assumes user is logged in.

        The parameter is mandatory for cmd.Cmd, but we ignore it.
        """

        response = self.fetch()
        if response == 1:
            print "Your session has expired."
        elif response == 2:
            print "Could not fetch messages. Please, try again."
        elif response == 3:
            print "Server timed out. Are you connected?"
        else:
            print response

    @check_authorization
    def do_join_group(self, group_id):
        """
        Adds the current logged in user to a group.

        :param group_id: The group to which current user will be added.
        """

        status = self.add_user_to_group(self.username, group_id)
        if status == 1:
            print "Your session has expired."
        elif status == 2:
            print "Could not add you to group {}. Please, try again.".format(group_id)
        elif status == 3:
            print "Server timed out. Are you connected?"
        else:
            print "You were added to group {} successfully.".format(group_id)

    @check_authorization
    def do_get_groups(self, wildcard='.*'):
        """
        Prints a list of groups matching a query, using a wildcard.
        Assumes user is logged in.

        :param wildcard: The wildcard used for matching; default is *
        """

        response = self.get_groups(wildcard)
        if response == 1:
            print "Your session has expired."
        elif response == 2:
            print "Could not get groups. Please, try again."
        elif response == 3:
            print "Server timed out. Are you connected?"
        else:
            print "These groups match your query:"
            print response

    @check_authorization
    def do_get_users(self, wildcard='.*'):
        """
        Prints a list of users matching a query, using a wildcard.
        Assumes user is logged in.

        :param wildcard: The wildcard used for matching; default is *
        """

        response = self.get_users(wildcard)
        if response == 1:
            print "Your session has expired."
        elif response == 2:
            print "Could not get users. Please, try again."
        elif response == 3:
            print "Server timed out. Are you connected?"
        else:
            print "These users match your query:"
            print response

    @check_authorization
    def do_delete_account(self, _):
        """
        Deletes the account for the current logged in user.
        Assumes user is logged in.

        The parameter is mandatory for cmd.Cmd, but we ignore it.
        """
        
        status = self.delete_account()
        if status == 1:
            print "Your session has expired."
        elif status == 2:
            print "Could not delete your account. Please, try again."
        elif status == 3:
            print "Server timed out. Are you connected?"
        else:
            self.loggedIn = False
            print "Account deleted successfully."
