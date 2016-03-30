import socket
import sys
import time
from rdtp.rdtp_client import RDTPClient
from rest.rest_client import RESTClient

def usage():
    """
    Simple usage function that is printed when the command line arguments
    are not valid.
    """
    print "Usage: python client.py <REST|RDTP>"
    exit()

def main():
    """
    Main routine of the program. By default, uses localhost and port 9999.
    This can be changed in this function. This checks the command line
    arguments, and starts up the appropriate chat_client according to
    user input. 

    Assumes that there is a single command line argument, which is simply 
    REST or RDTP.
    """
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

if __name__ == "__main__":
    main()
