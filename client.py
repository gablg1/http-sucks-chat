import socket
import sys

HOST, PORT = "localhost", 9999

data = " ".join(sys.argv[1:])

class RDTPClient():
    def connect(self, host, port):
        self.host = host
        self.port = port

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))

    def send(self, message):
        self.socket.sendall(message)

    def recv(self, max_len):
        return self.socket.recv(max_len)

    def close(self):
        self.socket.close()

# Create a socket (SOCK_STREAM means a TCP socket)

try:
    chat_client = RDTPClient()
    chat_client.connect(HOST, PORT)
    chat_client.send(data + "\n")

    # Connect to server and send data
    chat_client.send(data + "\n")

    # Receive data from the server and shut down
    received = chat_client.recv(1024)
finally:
    chat_client.close()

print "Sent:     {}".format(data)
print "Received: {}".format(received)
