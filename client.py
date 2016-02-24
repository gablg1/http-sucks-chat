import socket
import sys
import time
from rdtp_client import RDTPClient

HOST, PORT = "localhost", 9999

data = " ".join(sys.argv[1:])

chat_client = RDTPClient(HOST, PORT)

# Connect to server and send data
chat_client.connect()
chat_client.cmdloop()

print "Sent:     {}".format(data)
print "Received: {}".format(received)
