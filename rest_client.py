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

    def create_group(self, group_name):
        """Instructs server to create an account with some group_id."""
        data = {'data': {'group_name': group_name}}
        response = self.session.post(self.base_url + '/groups', json=data)
        r = response.json()

        if 'errors' in r:
            print r['errors']['title']
        else:
            print "Group successfully created!"

    def add_user_to_group(self, username, group_name):
        """Instructs server to add a user to a group."""
        data = {'data': {'username': username}}
        response = self.session.post(self.base_url + '/groups/' + group_name + '/users', json=data)
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

        self.session = requests.Session()

        # Login with new account
        self.session.auth = (username, password)
        response = self.session.post(self.base_url + '/login')
        r = response.json()

        if 'errors' in r:
            print r['errors']['title']
            return False
        
        self.username = r['data']['user']['username']
        self.session.auth = ('TOK', r['data']['user']['session_token'])
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

    def send_user(self, username, message):
        msg = {'data': {'message': message}}
        response = self.session.post(self.base_url + '/users/' + username + '/messages', json=msg)
        r = response.json()

        if 'errors' in r:
            print r['errors']['title']
        else:
            print "Your message has been sent!"

    def send_group(self, group_name, message):
        msg = {'data': {'message': message}}
        response = self.session.post(self.base_url + '/groups/' + group_name, json=msg)
        r = response.json()

        if 'errors' in r:
            print r['errors']['title']
        else:
            print "Your message has been sent!"

    def get_groups(self, wildcard):
        wildcard = {'wildcard': wildcard}
        response = self.session.get(self.base_url + '/groups', params=wildcard)
        r = response.json()

        if 'errors' in r:
            print r['errors']['title']
        else:
            return '\n'.join(r['data']['groups'])

    def delete_account(self):
        response = self.session.delete(self.base_url + '/users/' + self.username)
        r = response.json()

        if 'errors' in r:
            print r['errors']['title']
        else:
            print "Your account has been deleted. :("

    def fetch(self):
        """Fetch new messages from the server."""
        response = self.session.get(self.base_url + '/users/' + self.username + '/messages')
        r = response.json()

        if 'errors' in r:
            print r['errors']['title']
        else:
            return '\n'.join(r['data']['messages'])