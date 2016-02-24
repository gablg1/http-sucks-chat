import socket
import sys
from rdtp_client import RDTPClient

HOST, PORT = "localhost", 9999

data = " ".join(sys.argv[1:])

chat_client = RDTPClient(HOST, PORT)

try:
    # Connect to server and send data
    chat_client.connect()
    chat_client.send(data + "\n")

    # Receive data from the server and shut down
    received = chat_client.recv(1024)
finally:
    chat_client.close()

print "Sent:     {}".format(data)
print "Received: {}".format(received)
