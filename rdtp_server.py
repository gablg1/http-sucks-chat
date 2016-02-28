import socket
import select
from chat_server import ChatServer
from chat_server import UserKeyError
from chat_server import GroupExists
from chat_server import GroupDoesNotExist

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

    def serve_forever(self):
        # Starts listening
        self.socket.bind((self.host, self.port))
        self.socket.listen(MAX_PENDING_CLIENTS)
        print "RDTP Chat server listening on port %s" % self.port

        while 1:
            # This blocks until we are ready to read some socket
            ready_to_read,_,_ = select.select(self.sockets,[],[],0)

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
                    received = sock.recv(MAX_MSG_SIZE)
                    if received:
                        print 'Client message: %s' % (received)
                        self.handleMessage(sock, received)
                    else:
                        print 'Client [%s:%s] is offline. Bye bye.' % (sock.getpeername())
                    	assert(sock in self.sockets)
                    	self.sockets.remove(sock)

    def create_account(self, username, password, group_id = None):
        super(RDTPServer, self).create_account(username, password, group_id)
        self.user_info[username]['sock'] = None

    def kickout_user(self, username):
        """Kickout the current user."""
        sock = self.user_info[username]['sock']
        sock.sendall("You've been kicked, as someoen has logged into your account. You should really be using 2FA.")
        self.sockets.remove(sock)
        sock.close()

    def handleMessage(self, sock, message):
        args = message.split(':')

        assert(len(args) > 0)

        action = args[0]

        # As the command list grows, we could switch to a dictionary approach, since python lacks switches.
        # Would give O(1) command lookup by hashing.

        ################
        # Public actions
        ################
        if action == "username_exists":
            username = args[1]
            if self.username_exists(username):
                sock.sendall("1")
            else:
                sock.sendall("0")

        elif action == "create_account":
            username = args[1]
            password = args[2]
            self.create_account(username, password)

        elif action == "create_group":
            group_id = args[1]
            try:
                self.create_group(group_id)
                sock.sendall("1")
            except GroupExists:
                sock.sendall("0")

        elif action == "login":
            username = args[1]
            password = args[2]

            success, session_token = self.login(username, password)
            if success:
                self.user_info[username]['sock'] = sock
                sock.sendall(session_token)
            else:
                sock.sendall("0")

        elif action == "users_online":
            users = self.users_online()
            if len(users) == 0:
                sock.sendall('0')
            else:
                sock.sendall(':'.join(users))

        elif action == "add_to_group_current_user":
            session_token = args[1]
            group_id = args[2]

            if session_token in self.logged_in_users:
                try:
                    user = self.logged_in_users[session_token]
                    self.addUserToGroup(user["username"], group_id)
                    sock.sendall("1")
                except GroupDoesNotExist:
                    sock.sendall("2")
            else:
                sock.sendall("0")

        elif action == "add_to_group":
            username = args[1]
            group_id = args[2]

            try:
                self.addUserToGroup(username, group_id)
                sock.sendall("1")
            except GroupDoesNotExist:
                sock.sendall("0")

        elif action == "send_user":
            session_token = args[1]
            dest_user = args[2]
            message = args[3]

            if session_token in self.logged_in_users:
                try:
                    self.sendMessageToUser(message, dest_user)
                    sock.sendall("1")
                except UserKeyError:
                    sock.sendall("2")
            else:
                sock.sendall("0")

        elif action == "send_group":
            session_token = args[1]
            dest_group = args[2]
            message = args[3]

            if session_token in self.logged_in_users:
                try:
                    self.sendMessageToGroup(message, dest_group)
                    sock.sendall("1")
                except GroupKeyError:
                    sock.sendall("2")
            else:
                sock.sendall("0")

        #################################
        # Authentication required actions
        #################################
        elif action == "fetch":
            session_token = args[1]
            user = self.logged_in_users[session_token]
            self.deliverMessages(user["username"])

        elif action == "send":
        	self.sendMessageToGroup(args[2], int(args[1]))

        elif action == "logout":
            session_token = args[1]
            if session_token in self.logged_in_users:
                try:
                    user = self.logged_in_users[session_token]
                    del self.logged_in_users[user['session_token']]
                    user['logged_in'] = False
                    user['session_token'] = None
                    user['sock'] = None
                    sock.sendall("1")
                except UserKeyError:
                    sock.sendall("2")
            else:
                sock.sendall("0")
        else:
        	print "Action not found."

    def isOnline(self, user):
        return self.user_info[user]["logged_in"]

    def send(self, message, username):
        sock = self.user_info[username]['sock']
        try:
            sock.sendall(message)
        except:
            print 'Failed to send message to client [%s:%s]' % sock.getpeername()
