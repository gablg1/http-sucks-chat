from chat.chat_client import ChatClient
from functools import wraps
import requests
import sys

def check_session(f):
    """
    Wrapper that guarantees that there is a section in place.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        if args[0].session is None:
            print "No current session. Please, login to perform this action."
            return 1

        return f(*args, **kwargs)
    return wrapper

class RESTClient(ChatClient):
    """
    Implements a subclass of ChatClient, that will use REST as its
    communication protocol.

    This class uses the Requests library to make HTTP Requests to servers.
    We use the methods get(), post(), delete() and the Session functionality
    from that library. The documentation for Requests can be found here:
    [http://requests.readthedocs.org/en/master/]
    """

    def __init__(self, host, port):
        """
        Initializes a ChatClient on the given host and port. Defines
        some class variables that will be used later on, such as session,
        username and base_url.

        :param host: The host where this client should connect to
        :param port: The port that this client should connect to
        """

        ChatClient.__init__(self, host, port)
        self.username = None
        self.session = None
        self.base_url = 'http://' + host + ':' + str(port)

    ###########
    ## USERS ##
    ###########

    def create_account(self, username, password):
        """
        Instructs server to create an account with given username and password.

        :param username: The username to create
        :param password: The corresponding password

        :return: 0 on success, or 2 if the username already exists.
        """
        credentials = {'username': username, 'password': password}

        response = requests.post(self.base_url + '/users', json=credentials)
        r = response.json()

        if 'errors' in r:
            return self.__handle_error(r)

        return 0

    def login(self, username, password):
        """
        Login with given username and password. This also sets up a
        Requests session with the appropriate session token.
        
        :param username: The username to create
        :param password: The corresponding password

        :return: 0 on success, 1 if the login credentials do not match,
        and 2 for any other error (see __handle_error).
        """
        # First logout of current account
        if self.session is not None:
            self.logout

        self.session = requests.Session()

        # Login with new account
        self.session.auth = (username, password)
        response = self.session.post(self.base_url + '/login')
        r = response.json()

        if 'errors' in r:
            return self.__handle_error(r)

        try:
            self.username = r['data']['user']['username']
            self.session.auth = ('TOK', r['data']['user']['session_token'])
        except:
            return 1

        return 0

    @check_session
    def logout(self):
        """
        Logout of the chat service. Assumes that a session is already in place.

        :return: 0 on success, 1 if there is invalid, 2 for 
        other possible errors (see __handle_error).
        """

        response = self.session.post(self.base_url + '/logout')
        r = response.json()

        if 'errors' in r:
            return self.__handle_error(r)

        self.username = None
        self.session_token = None

        return 0

    @check_session
    def delete_account(self):
        """
        Delete an account at this chat service. Assumes that a session
        is already in place, and tries to delete the account currently
        logged in.

        :return: 0 on success, 1 if the session is invalid, 2 for
        other possible errors (see __handle_error).
        """

        response = self.session.delete(self.base_url + '/users/' + self.username)
        r = response.json()

        if 'errors' in r:
            return self.__handle_error(r)

        return 0

    @check_session
    def send_user(self, username, message):
        """
        Send a message to a user. Assumes that a session is already in place,
        and tries to send the message with the account currently logged in.

        :param username: The username to which the message will be sent
        :param message: The message that will be sent

        :return: 0 on success, 1 if the session is invalid, 2 for other 
        possible errors (see __handle_error).
        """

        msg = {'data': {'message': message}}
        response = self.session.post(self.base_url + '/users/' + username + '/messages', json=msg)
        r = response.json()

        if 'errors' in r:
            return self.__handle_error(r)

        return 0

    @check_session
    def fetch(self):
        """
        Fetch new messages from the server. Assumes that a session is already in place,
        and tries to fetch messages for the currently logged in account.

        :return: On success, returns a string containing all of the messages (or 
        "No new messages".) On failure, returns 1 if there was no session in place, and
        2 for other possible errors (see __handle_error).
        """

        response = self.session.get(self.base_url + '/users/' + self.username + '/messages')
        r = response.json()

        if 'errors' in r:
            return self.__handle_error(r)

        messages = r['data']['messages']

        if messages == []:
            return "No new messages."

        try:
            ret = []
            for msg in messages:
                if msg['from_group_name'] is None:
                    ret.append(msg['from_username'] + ' >>> ' + msg['message'])
                else:
                    ret.append(msg['from_username'] + ' @ ' + msg['from_group_name'] + ' >>> ' + msg['message'])
        except:
            return 2

        return '\n'.join(ret)

    ############
    ## GROUPS ##
    ############

    @check_session
    def create_group(self, group_name):
        """
        Creates a group with some given name. Assumes that a session is already in place.

        :param group_name: The name of the group to be created

        :return: 0 on success, 1 if the session is invalid, 2 for other possible
        errors (for instance if the groupname is already taken; see __handle_error).
        """
        data = {'data': {'group_name': group_name}}
        response = self.session.post(self.base_url + '/groups', json=data)
        r = response.json()

        if 'errors' in r:
            return self.__handle_error(r)

        return 0

    @check_session
    def add_user_to_group(self, username, group_name):
        """
        Adds a user to a group. Assumes that a session is already in place;
        if there is no session, no users can be added to groups (namely, only
        logged in users can modify groups).

        :param username: The username of the user to be added
        :param group_name: The name of the group to which we should add

        :return: 0 on success, 1 if the session is invalid, 2 for other possible
        errors (for instance if the groupname is already taken; see __handle_error).
        """

        data = {'data': {'username': username}}
        response = self.session.post(self.base_url + '/groups/' + group_name + '/users', json=data)
        r = response.json()

        if 'errors' in r:
            return self.__handle_error(r)

        return 0

    @check_session
    def send_group(self, group_name, message):
        """
        Send a message to a group. Assumes that a session is already in place,
        and tries to send the message with the account currently logged in.

        :param group_name: The group to which the message will be sent
        :param message: The message that will be sent

        :return: 0 on success, 1 if the session is invalid, 2 for other 
        possible errors (see __handle_error).
        """

        msg = {'data': {'message': message}}
        response = self.session.post(self.base_url + '/groups/' + group_name + '/messages', json=msg)
        r = response.json()

        if 'errors' in r:
            return self.__handle_error(r)

        return 0

    @check_session
    def get_groups(self, wildcard):
        """
        Get all groups matching wildcard. Assumes that a session is already in place;
        only logged in users can perform this operation.

        :param wildcard: The regular expression wildcard that we want to use for 
        searching groups

        :return: On success, returns a string containing the names of the groups. 
        On failure, return 1 if the session is invalid and 2 for other 
        possible errors (see __handle_error).
        """

        wildcard = {'wildcard': wildcard}
        response = self.session.get(self.base_url + '/groups', params=wildcard)
        r = response.json()

        if 'errors' in r:
            return self.__handle_error(r)

        try:
            groups = r['data']['groups']
        except:
            return 2

        return '\n'.join(groups)

    @check_session
    def get_users(self, wildcard):
        """
        Get all users matching wildcard. Assumes that a session is already in place;
        only logged in users can perform this operation.

        :param wildcard: The regular expression wildcard that we want to use for 
        searching users

        :return: On success, returns a string containing the names of the users. 
        On failure, return 1 if the session is invalid and 2 for other 
        possible errors (see __handle_error).
        """

        wildcard = {'wildcard': wildcard}
        response = self.session.get(self.base_url + '/users', params=wildcard)
        r = response.json()

        if 'errors' in r:
            return self.__handle_error(r)

        try:
            users = r['data']['users']
        except:
            return 2

        return '\n'.join(users)

    ############
    ## HELPER ##
    ############
    def __handle_error(self, r):
        """
        Helper function that will parse the response by the HTTP server
        and return an appropriate error code (within the scope of ChatClient).

        The methods defined in ChatClient will use this error code to print out
        error messages to users. 

        :param r: The response given by the HTTP server that we are connected to
        :return: 1 for authentication errors, and 2 for any other error.
        """
        
        try:
            status_code = r['errors']['status_code']
        except:
            return 2

        if status_code == 401:
            return 1

        # 200 here means a conflict: create_group or create_account
        if status_code == 200:
            return 2

        return 2


