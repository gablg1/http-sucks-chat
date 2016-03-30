import select
import socket

class ClientDied(Exception):
    def __str__(self):
        return "The client died."

##################################
### Real Data Transfer Protocol
##################################
#
# Magic number (1 byte) / Version (1 byte) /  Action (1 byte) /
# Length (1 byte) / Message (Length bytes)

RDTP_HEADER_LENGTH = 5
RDTP_MAGIC = unichr(0x42)
RDTP_VERSION = unichr(1)
ARG_LEN_MAX = 256

def recv_message(sock):
    """
    recv_message: receives a message formatted according to RDTP from a ready socket

    Parameters
    sock: a socket object. Belongs to either a client listening for a server response on its
        listener thread, or a server that has blocked on a set of sockets waiting for them
        to be ready to read

    Assumes the message is in the format of RDTP.
    Assumes no dropped bytes.

    Returns the action, status of the response, and the actual message delimited by colons
    """
    # get the first 3 bytes which are supposed to be part of the preamble
    header = recv_nbytes(sock, RDTP_HEADER_LENGTH)
    assert(len(header) == RDTP_HEADER_LENGTH)

    magic, version, status, action_len, msg_len = header[0], header[1], header[2], header[3], header[4]
    assert(magic == RDTP_MAGIC)
    assert(version == RDTP_VERSION)

    # read in the expected message
    action = recv_nbytes(sock, ord(action_len))
    message = recv_nbytes(sock, ord(msg_len))
    status_code = ord(status)

    return action, status_code, message

def recv(sock):
    """
    recv: receives a message on a socket, parses the output, and returns the different parts

    Parameters:
    sock: A socket that has a message ready to be read

    the final part of the message is assumed to be colon-delimited

    Returns the action, response status, and a list of arguments for the action
    """
    action, status, message = recv_message(sock)
    args = message.split(':')
    return action, status, args

def send(sock, action, status, *args):
    """
    send acts as a wrapper for send_message. It just makes sure that the parts of the message
    are joined by colons for later parsing.
    """
    send_message(sock, action, status, ':'.join(args))

def send_message(sock, action, status, message):
    """
    send_message: sends a message according to the RDTP protocol along the provided socket object

    Parameters:
    sock: the socket object along which to send the message
    action: specifies the specific action the sender wants the receiver to take. less than ARG_LEN_MAX.
    Actions for the server to send specify whether the message is a message from another user or a server
    response to a previously requested action. Actions for the client to send are different commands available
    to the client.
    status: Different possible error code. The client always sends zero as a status, while the server is
    free to send any code that the client would understand.

    Assumes that message is colon-delimited.
    """
    msg_len = len(message)
    if msg_len > ARG_LEN_MAX:
    	print 'Message too long'
    	return False

    action_len = len(action)
    if action_len > ARG_LEN_MAX:
    	print 'Action too long'
    	return False

    # Constructs RDTP message
    to_send = RDTP_MAGIC + RDTP_VERSION + unichr(status)
    to_send += unichr(action_len) + unichr(msg_len)
    to_send += action
    to_send += message
    assert(len(to_send) == RDTP_HEADER_LENGTH + action_len + msg_len)

    # Sends the actual message
    sock.sendall(to_send)


def recv_nbytes(sock, n):
    """
    recv_nbytes reads in a certain number of bytes from a socket. Blocks until it receives all requested bytes

    Parameters:
    sock: socket to receive message from
    n: number of bytes to read

    Assumes messages are not dropped (otherwise blocks forever)
    """
    bytes_received = 0
    received = ""
    # keep on readin' until we get what we expected
    while bytes_received < n:
        ready_to_read,_,_ = select.select([sock],[],[])
        data = sock.recv(1, socket.MSG_PEEK)

        if len(data) == 0:
            raise ClientDied
        else:
            assert(ready_to_read != [])
            new_recv = sock.recv(n - bytes_received)
            bytes_received += len(new_recv)
            received += new_recv
    assert(bytes_received == len(received))
    return received

