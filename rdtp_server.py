import socket
import select
from chat_server import ChatServer
from chat_server import GroupKeyError
from chat_server import UserKeyError
from chat_server import UserNotLoggedInError
from chat_server import GroupExists
from chat_server import GroupDoesNotExist
import rdtp_common

MAX_MSG_SIZE = 1024
MAX_PENDING_CLIENTS = 10

class RDTPServer(ChatServer):
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
        # Starts listening
        self.socket.bind((self.host, self.port))
        self.socket.listen(MAX_PENDING_CLIENTS)
        print "RDTP Chat server listening on port %s" % self.port

        while 1:
            # This blocks until we are ready to read some socket
            ready_to_read,_,_ = select.select(self.sockets,[],[])

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
                    action, message = rdtp_common.recv(sock)
                    if action:
                        print 'Client action: %s,  Client message: %s' % (action, message)
                        self.handle_message(sock, action, message)
                    else:
                        print 'Client [%s:%s] is offline. Bye bye.' % (sock.getpeername())
                        assert(sock in self.sockets)
                        self.sockets.remove(sock)

    def create_account(self, username, password):
        super(RDTPServer, self).create_account(username, password)
        self.sockets_by_user[username] = None

    def kickout_user(self, username):
        """Kickout the current user."""
        try:
            sock = self.sockets_by_user[username]
            sock.sendall('M' + "You've been kicked, as someone has logged into your account. You should really be using 2FA.")
            if sock in self.sockets:
                self.sockets.remove(sock)
                sock.close()
        except KeyError:
            print "Could not kickout the previous user, probably because he/she is leftover from a previous instantation of the server."

    def handle_message(self, sock, action, message):
        args = message.split(':')
        assert(len(args) > 0)
        # As the command list grows, we could switch to a dictionary approach, since python lacks switches.
        # Would give O(1) command lookup by hashing.

        ################
        # Public actions
        ################
        if action == "username_exists":
            username = message
            if self.username_exists(username):
                self.send(sock, "R", "1")
            else:
                self.send(sock, "R", "0")

        elif action == "create_account":
            username = args[0]
            password = args[1]
            self.create_account(username, password)

        elif action == "create_group":
            group_id = args[0]
            try:
                self.create_group(group_id)
                self.send(sock, "R", "0")
            except GroupExists:
                self.send(sock, "R", "1")

        elif action == "login":
            username = args[0]
            password = args[1]

            success, session_token = self.login(username, password)
            if success:
                self.sockets_by_user[username] = sock
                self.send(sock, "R", "0")
            else:
                self.send(sock, "R", "0")

        elif action == "users_online":
            users = self.users_online()
            if len(users) == 0:
                self.send(sock, "R", "0")
            else:
                self.send(sock, "R", ":".join(users))

        elif action == "add_to_group_current_user":
            session_token = args[0]
            group_name = args[1]

            try:
                username = self.username_for_session_token(session_token)
                self.add_user_to_group(username, group_name)
                self.send(sock, "R", "0")
            except UserNotLoggedInError:
                self.send(sock, "R", "1")
            except GroupDoesNotExist:
                self.send(sock, "R", "2")

        elif action == "add_to_group":
            username = args[0]
            group_name = args[1]

            try:
                self.add_user_to_group(username, group_name)
                self.send(sock, "R", "0")
            except GroupDoesNotExist:
                self.send(sock, "R", "1")

        elif action == "send_user":
            session_token = args[0]
            dest_user = args[1]
            message = args[2]

            try:
                self.send_message_to_user(message, dest_user)
                self.send(sock, "R", "0")
            except UserKeyError:
                self.send(sock, "R", "1")

            # TODO: Send C0 if user is not logged in.
            # Will do this after we implement keeping track of sender username.

        elif action == "send_group":
            session_token = args[0]
            dest_group = args[1]
            message = args[2]

            try:
                self.send_message_to_group(message, dest_group)
                self.send(sock, "R", "0")
            except GroupKeyError:
                self.send(sock, "R", "1")
            # TODO: Send C0 if user is not logged in.
            # Will do this after we implement keeping track of sender username.

        elif action == "get_users_in_group":
            group = args[0]
            users = self.get_users_in_group(group)
            if len(users) == 0:
                self.send(sock, "R", "0")
            else:
                self.send(sock, "R", ":".join(users))

        #################################
        # Authentication required actions
        #################################
        elif action == "fetch":
            session_token = args[0]
            try:
                username = self.username_for_session_token(session_token)
                messages = self.get_user_queued_messages(username)
                if len(messages) == 0:
                    self.send(sock, "R", "0")
                else:
                    messageString = '\n'.join(messages)
                    self.send(sock, "M", messageString)
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
                self.send(sock, "R", "0")
            except UserKeyError:
                self.send(sock, "R", "1")
            except UserNotLoggedInError:
                self.send(sock, "R", "2")
        else:
            print "Action not found."


    def send(self, sock, action, message):
        try:
            rdtp_common.send(sock, "M", message)
        except:
            print 'Failed to send message to client [%s:%s]' % sock.getpeername()
