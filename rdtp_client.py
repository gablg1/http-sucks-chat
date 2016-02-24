import socket
import sys
import select
from chat_client import ChatClient

class RDTPClient(ChatClient):
    def __init__(self, host, port):
        ChatClient.__init__(self, host, port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        self.socket.connect((self.host, self.port))


    def send(self, message):
        try:
            self.socket.sendall(message)
        except:
            print "Couldn't send message. Assuming server disconnected."
            self.close()

    def recv(self, max_len):
        ready_to_read,_,_ = select.select([self.socket],[],[],0.2)
        if ready_to_read == []:
        	return 'No new messages.'
        return self.socket.recv(max_len)


    def fetch(self):
        return self.recv(1024)


    def close(self):
        self.socket.close()
