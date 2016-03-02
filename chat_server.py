from abc import abstractmethod
from chat_db import ChatDB
from chat_db import UsernameExists
import socket
import select
from random import choice
from string import ascii_uppercase
import re

class ChatServer(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.chatDB = ChatDB()

    def kickout_user(self, username):
        """Kickout the current user. Implementation specific."""

    def create_account(self, username, password):
        """Create an account with given username and password."""
        try:
            return self.chatDB.create_account(username, password)
        except UsernameExists:
            print "caught usernameExists in chat_server.create_account"
            return False

    def create_group(self, group_name):
        return self.chatDB.create_group(group_name)

    def login(self, username, password):
        return self.chatDB.login(username, password, self.kickout_user)

    def logout(self, username):
        """Tell MongoDB that a user has been logged out."""
        return self.chatDB.logout(username)

    def users_online(self):
        """Return usernames of users who are logged in."""
        return self.chatDB.users_online()

    def get_users_in_group(self, group_name):
        """Return usernames of users who are in this group."""
        return self.chatDB.get_users_in_group(group_name)

    def add_user_to_group(self, username, group_name):
        return self.chatDB.add_user_to_group(username, group_name)

    def send_message_to_group(self, session_token, message, group_name):
        """Send message a group with this group_name."""
        users = self.chatDB.get_users_in_group(group_name)

        for username in users:
            self.send_or_queue_message(session_token, message, username, group_name)

    def send_or_queue_message(self, session_token, message, username, group_name = None):
        """send message to a user with this username."""
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

    def is_online(self, username):
        """Check if a user is online. 
        Should be overriden in some server implementations if "logged in"
        scheme is senseless."""
        return self.chatDB.is_online(username)

    def get_user_queued_messages(self, username):
        """Get all messages queued for some user."""
        return self.chatDB.get_user_queued_messages(username)

    def clear_user_message_queue(self, username):
        """Clear all messages queued for some user."""
        return self.chatDB.clear_user_message_queue(username)

    def delete_account(self, username):
        """Deletes the account corresponding to a username."""
        return self.chatDB.delete_account(username)

    def username_for_session_token(self, session_token):
        return self.chatDB.username_for_session_token(session_token)

    def get_users(self, query):
        """Return all users who match some regex query."""
        return self.chatDB.get_users(query)

    def get_groups(self, query):
        """Return all groups who match some regex query."""
        return self.chatDB.get_groups(query)
