import socket
import select

MAX_MSG_SIZE = 1024
MAX_PENDING_CLIENTS = 10

class RDTPServer():
    def __init__(self, host, port):
        self.host = host
        self.port = port

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


    def handleMessage(self, src, message):
        # Sends message to everyone but the source of the message
        for sock in self.sockets:
            if sock != src and sock != self.socket:
                try:
        		    sock.sendall(message)
                except:
                    print 'Failed to send message to client [%s:%s]' % sock.getpeername()


