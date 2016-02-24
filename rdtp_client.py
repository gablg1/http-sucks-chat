import socket
import sys
from chat_client import ChatClient

class RDTPClient(ChatClient):
    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))

    def send(self, message):
        self.socket.sendall(message)

    def recv(self, max_len):
        return self.socket.recv(max_len)

    def close(self):
        self.socket.close()
