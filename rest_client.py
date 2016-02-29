import requests
import sys
from chat_client import ChatClient
MAX_RECV_LEN = 1024

class RESTClient(ChatClient):
    def __init__(self, host, port):
        ChatClient.__init__(self, host, port)
        self.username = None
        self.session = None
        self.base_url = 'http://' + host + ':' + str(port)

    ##################################
    ### Connectivity -- ALL HANDLED BY REQUESTS
    ##################################


    ##################################
    ### Abstract Method Implementation
    ##################################

    def create_account(self, username, password):
        """Instructs server to create an account with given username and password."""
        credentials = {'username': username, 'password': password}
        
        response = requests.post(self.base_url + '/users', json=credentials)
        r = response.json()

        if 'errors' in r:
            print r['errors']['title']
            return False

        print "Account successfully created!"
        return True

    def create_group(self, group_id):
        """Instructs server to create an account with some group_id."""
        data = {'data': {'group_id': group_id}}
        response = self.session.post(self.base_url + '/groups', json=data)
        r = response.json()

        if 'errors' in r:
            print r['errors']['title']
        else:
            print "Group successfully created!"

    def add_user_to_group(self, username, group_id):
        """Instructs server to add a user to a group."""
        data = {'data': {'username': username}}
        response = self.session.post(self.base_url + '/groups/' + str(group_id) + '/users', json=data)
        r = response.json()

        if 'errors' in r:
            print r['errors']['title']
        else:
            print "Successfully added user to the group!"

    def login(self, username, password):
        """Login with given username and password.
        Returns boolean."""
        # First logout of current account
        if self.session is not None:
        	self.logout
        	return

        self.session = requests.Session()

        # Login with new account
        self.session.auth = (username, password)
        response = self.session.post(self.base_url + '/login')
        r = response.json()

        if 'errors' in r:
            print r['errors']['title']
            return False
        
        self.username = username
        self.session.auth = ('TOK', response.json()['session_token'])
        print "Loged in successfully as {}!".format(self.username)
        return True

    def logout(self):
        """Logout of http-sucks-chat.
        Returns boolean."""
        if self.session is None:
            return False

        response = self.session.post(self.base_url + '/logout')
        r = response.json()

        if 'errors' in r:
            # code for error handling
            print r['errors']['title']
            return False
 
        print "See you later, {}!".format(self.username)
        self.username = None
        self.session_token = None
        return True

    def users_online(self):
        """Returns list of users logged into http-sucks-chat."""
        response = self.session.get(self.base_url + '/users')
        r = response.json()

        if 'errors' in r:
            print r['errors']['title']
        else:
            return r['data']['users']

    def send_user(self, user_id, message):
        msg = {'data': {'message': message}}
        response = self.session.post(self.base_url + '/users/' + str(user_id), json=msg)
        r = response.json()

        if 'errors' in r:
            print r['errors']['title']
        else:
            print "Your message has been sent!"

    def send_group(self, group_id, message):
        msg = {'data': {'message': message}}
        response = self.session.post(self.base_url + '/groups/' + str(group_id), json=msg)
        r = response.json()

        if 'errors' in r:
            print r['errors']['title']
        else:
            print "Your message has been sent!"

    def fetch(self):
        """Fetch new messages from the server."""
        response = self.session.get(self.base_url + '/users/' + self.username)
        r = response.json()

        if 'errors' in r:
            print r['errors']['title']
        else:
            return '\n'.join(r['data']['messages'])

        return self.recv(MAX_RECV_LEN)
