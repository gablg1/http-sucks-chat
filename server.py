import socket
import sys
from rdtp.rdtp_server import RDTPServer
from rest.rest_server import RESTServer

def usage():
    """
    Simple usage function that is printed when the command line arguments
    are not valid.
    """
    print "Usage: python server.py <REST|RDTP>"
    exit()

def main():
    """
    Main routine of the program. By default, uses localhost and port 9999.
    This can be changed in this function. This checks the command line
    arguments, and starts up the appropriate chat_server according to
    user input.

    Assumes that there is a single command line argument, which is simply 
    REST or RDTP.
    """
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

if __name__ == "__main__":
    main()
