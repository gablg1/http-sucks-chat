import socket
import sys
from rdtp.rdtp_server import RDTPServer
from rest.rest_server import RESTServer

def usage():
	print "Usage: python server.py <REST|RDTP>"
	exit()

HOST, PORT = "localhost", 9999

if len(sys.argv) != 2:
	usage()

if sys.argv[1].upper() == 'REST':
	chat_server = RESTServer(HOST, PORT)
elif sys.argv[1].upper() == 'RDTP':
	chat_server = RDTPServer(HOST, PORT)
else:
	usage()

chat_server.serve_forever()
