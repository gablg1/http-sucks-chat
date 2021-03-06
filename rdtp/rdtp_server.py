import socket
import select
from chat.chat_server import ChatServer
from chat.chat_db import GroupKeyError
from chat.chat_db import UserKeyError
from chat.chat_db import UserNotLoggedInError
from chat.chat_db import GroupExists
from chat.chat_db import GroupDoesNotExist
from chat.chat_db import UsernameExists
import rdtp_common
from rdtp_common import ClientDied

MAX_MSG_SIZE = 1024
MAX_PENDING_CLIENTS = 10

class RDTPServer(ChatServer):
    """
    Implements a ChatServer using the RDTP protocol.

    This class uses the Python-included socket and select libraries.
    These are standard ways to do networking, and are considerably 
    low-level.
    """
    
    def __init__(self, host, port):
        ChatServer.__init__(self, host, port)

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Because of this line, recv and send won't block and will raise
        # an error if they fail to send immediately.
        # Because of the select.select, we can assume every recv
        # will work correctly, but we have to try, except all sends
        self.socket.setblocking(0)

        # Magic to make socket reuse local addresses.
        # http://pubs.opengroup.org/onlinepubs/7908799/xns/getsockopt.html
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.sockets = [self.socket]
        self.sockets_by_user = {}

    def serve_forever(self):
        """
        serve_forever is a listener that continuously waits for open connections with it
        and handles any incoming requests. Blocks on all of its currently open connections once
        it handles currently waiting responses.
        """

        self.socket.bind((self.host, self.port))
        self.socket.listen(MAX_PENDING_CLIENTS)
        print "RDTP Chat server listening on port %s" % self.port

        while 1:
            # This blocks until we are ready to read some socket
            ready_to_read,_,_ = select.select(self.sockets,[],[],3)

            for sock in ready_to_read:
                # New client connection!
                # we accept the connection and get a new socket
                # for it
                if sock == self.socket:
                    new_client_sock, client_addr = sock.accept()
                    self.sockets.append(new_client_sock)
                    print 'New client connection with address [%s:%s]' % client_addr
                # Old client wrote us something. It must be
                # a message!
                else:
                    try:
                        action, status, args = rdtp_common.recv(sock)
                    except ClientDied:
                        self.sockets.remove(sock)
                        continue

                    if action:
                        print 'Client action: %s' % (action)
                        self.handle_request(sock, action, args)
                    else:
                        print 'Client [%s:%s] is offline. Bye bye.' % (sock.getpeername())
                        assert(sock in self.sockets)
                        self.sockets.remove(sock)

    def create_account(self, username, password):
        """
        create_account attempts to create an account for a client. Initalizes a slot for a socket for the user
        Uses mongoDB's interface to create an account by adding it to the database

        :param username: a string, no length to limit except by the RDTP protocol
        :param password: a string, no length to limit except by RDTP protocol

        :return On success, returns True. On Failure, returns UsernameExists error
        """
        self.sockets_by_user[username] = None
        super(RDTPServer, self).create_account(username, password)

    def kickout_user(self, username):
        """Kickout the current user. Used when a client logs in from a different place"""
        try:
            sock = self.sockets_by_user[username]
            self.send(sock, 'M', 0, "You've been kicked, as someone has logged into your account. You should really be using 2FA.")
            if sock in self.sockets:
                self.sockets.remove(sock)
                sock.close()
        except KeyError:
            print "Could not kickout the previous user, probably because he/she is leftover from a previous instantation of the server."

    def handle_request(self, sock, action, args):
        """
        Dispatcher that actually calls the appropriate method for the requested client action
        For responses, a status code of 0 is assumed to be all good for the client.

        :param sock: the socket object belonging to the client that sent the message
        :param action: a string corresponding to the action the client wishes to take
        :param args: a list of strings corresponding to arguments required by the action

        """
        print "Handling request. Action: {0}, args: {1}".format(action, args)
        assert(len(args) > 0)
        # As the command list grows, we could switch to a dictionary approach, since python lacks switches.
        # Would give O(1) command lookup by hashing.

        ################
        # Public actions
        ################
        if action == "username_exists":
            username = args[0]
            if not self.username_exists(username):
                self.send(sock, "R", 0)
            else:
                self.send(sock, "R", 1)

        elif action == "create_account":
            username = args[0]
            password = args[1]

            try:
                self.create_account(username, password)
                self.send(sock, "R", 0)
            except UsernameExists:
                self.send(sock, "R", 2)

        elif action == "create_group":
            group_id = args[0]

            try:
                self.create_group(group_id)
                self.send(sock, "R", 0)
            except GroupExists:
                self.send(sock, "R", 2)

        elif action == "login":
            username = args[0]
            password = args[1]

            success, session_token = self.login(username, password)
            if success:
                self.sockets_by_user[username] = sock
                self.send(sock, "R", 0, session_token)
            else:
                self.send(sock, "R", 1)

        elif action == "add_to_group_current_user":
            session_token = args[0]
            group_name = args[1]

            try:
                username = self.username_for_session_token(session_token)
                self.add_user_to_group(username, group_name)
                self.send(sock, "R", 0)
            except UserNotLoggedInError:
                self.send(sock, "R", 1)
            except GroupDoesNotExist:
                self.send(sock, "R", 2)

        elif action == "add_to_group":
            username = args[0]
            group_name = args[1]

            try:
                self.add_user_to_group(username, group_name)
                self.send(sock, "R", 0)
            except GroupDoesNotExist:
                self.send(sock, "R", 2)

        elif action == "send_user":
            session_token = args[0]
            dest_user = args[1]
            message = args[2]

            try:
                self.send_or_queue_message(session_token, message, dest_user)
                self.send(sock, "R", 0)
            except UserKeyError:
                self.send(sock, "R", 2)

            # TODO: Send C0 if user is not logged in.
            # Will do this after we implement keeping track of sender username.

        elif action == "send_group":
            session_token = args[0]
            dest_group = args[1]
            message = args[2]

            try:
                self.send_message_to_group(session_token, message, dest_group)
                self.send(sock, "R", 0)
            except GroupDoesNotExist:
                self.send(sock, "R", 2)
            # TODO: Send C0 if user is not logged in.
            # Will do this after we implement keeping track of sender username.

        elif action == "get_groups":
            wildcard = args[0]
            if wildcard is None or wildcard == '':
                wildcard = '*'

            groups = [str(group['name']) for group in self.get_groups(wildcard)]
            if len(groups) == 0:
                self.send(sock, "R", 0)
            else:
                self.send(sock, "R", 0, *groups)

        elif action == "get_users":
            wildcard = args[0]
            if wildcard is None or wildcard == '':
                wildcard = '*'

            users = [str(user['username']) for user in self.get_users(wildcard)]
            if len(users) == 0:
                self.send(sock, "R", 0)
            else:
                self.send(sock, "R", 0, *users)

        #################################
        # Authentication required actions
        #################################
        elif action == "fetch":
            session_token = args[0]
            try:
                username = self.username_for_session_token(session_token)
                messages = self.get_user_queued_messages(username)
                if len(messages) == 0:
                    self.send(sock, "R", 0)
                else:
                    ret = []
                    for message in messages:
                        if message['from_group_name'] is None:
                            ret.append(message['from_username'] + ' >>> ' + message['message'])
                        else:
                            ret.append(message['from_username'] + ' @ ' + message['from_group_name'] + ' >>> ' + message['message'])

                    messageString = '\n'.join(ret)
                    self.send(sock, "R", 0, messageString)
                    self.clear_user_message_queue(username)
            except UserNotLoggedInError:
                print "Could not deliver messages to client with session_token {} because this client is not logged in.".format(session_token)

        elif action == "send":
            self.send_message_to_group(args[2], int(args[1]))

        elif action == "logout":
            session_token = args[0]
            try:
                username = self.username_for_session_token(session_token)
                self.logout(username)
                del self.sockets_by_user[username]
                self.send(sock, "R", 0)
            except UserKeyError:
                self.send(sock, "R", 1)
            except UserNotLoggedInError:
                self.send(sock, "R", 2)
        else:
            print "Action not found."

    def send_user(self, message, from_username, username, group_name = None):
        """
        send a user (or a group!) a message. Does not return.

        Parameters:
        :param message: The actual message. Assumed to be less than the permitted message length by RDTP
        :param from_username: the sender's name
        :param username: the receiver's name
        :param group_name: Default none, but can specify a pre-existing group
        """
        user_sock = self.sockets_by_user[username]
        rdtp_message = ""
        if group_name:
            rdtp_message = "{0} @ {1} >>> {2}".format(from_username, group_name, message)
        else:
            rdtp_message = "{0} >>> {1}".format(from_username, message)

        if message == "you don't deserve to live":
            self.send(user_sock, "KILL", 0, "")
        else:
            self.send(user_sock, "M", 0, rdtp_message)

    def send(self, sock, action, status, *args):
        """
        See rdtp_common file for more details on send.
        """
        try:
            rdtp_common.send(sock, action, status, *args)
        except Exception as error:
            print 'Failed to send message to client.'
            print error
