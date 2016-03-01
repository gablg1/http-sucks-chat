import select

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

    return status, action, message

def recv(sock):
    status, action, message = recv_message(sock)
    args = message.split(':')
    return status, action, args

def send(sock, status, action, *args):
    send_message(sock, status, action, ':'.join(args))

def send_message(sock, status, action, message):
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
    bytes_received = 0
    received = ""
    # keep on readin' until we get what we expected
    while bytes_received < n:
        ready_to_read,_,_ = select.select([sock],[],[])
        assert(ready_to_read != [])
        new_recv = sock.recv(n - bytes_received)
        bytes_received += len(new_recv)
        received += new_recv
    assert(bytes_received == len(received))
    return received

