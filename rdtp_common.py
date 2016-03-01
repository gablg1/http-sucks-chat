import select

##################################
### Real Data Transfer Protocol
##################################
#
# Magic number (1 byte) / Version (1 byte) /  Action (1 byte) /
# Length (1 byte) / Message (Length bytes)

RDTP_HEADER_LENGTH = 4
RDTP_MAGIC = 0x42
RDTP_VERSION = 1

def recv(sock):
    # get the first 3 bytes which are supposed to be part of the preamble
    header = recv_nbytes(sock, RDTP_HEADER_LENGTH)
    assert(len(header) == header)

    magic, version, action, length = header[0], header[1], header[2], header[3]
    assert(magic == RDTP_MAGIC)
    assert(version == RDTP_VERSION)

    # read in the expected message
    message = recv_nbytes(sock, length)
    return action, message

def send(sock, action, message):
    msg_len = len(message)
    if msg_len > MSG_LEN_MAX:
    	print 'Message too long'
    	return False

    if type(action) is not char:
    	print 'Action should be a character'
    	return False

    # Constructs RDTP message
    to_send = unichr(RDTP_MAGIC) + unichr(RDTP_VERSION) + action + unichr(msg_len)
    to_send += message
    assert(len(to_send) == RDTP_HEADER_LENGTH + msg_len)

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

