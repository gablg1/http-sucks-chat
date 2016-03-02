import socket
import sys
import time
from rdtp_client import RDTPClient
from rest_client import RESTClient

def usage():
	print "Usage: python client.py <REST|RDTP>"
	exit()

HOST, PORT = "localhost", 9999

if len(sys.argv) == 1:
	usage()

if sys.argv[1].upper() == 'REST':
	chat_client = RESTClient(HOST, PORT)
elif sys.argv[1].upper() == 'RDTP':
	chat_client = RDTPClient(HOST, PORT)
	chat_client.connect()
else:
	usage()

chat_client.cmdloop()
