import select

def recv(sock):
    # size of the first part of the protocol
    preamble_size = 3
    # block until available
    ready_to_read,_,_ = select.select([sock],[],[])
    # get the first 3 bytes which are supposed to be part of the preamble
    proto_preamble = sock.recv(preamble_size)
    assert(len(proto_preamble) == 3)
    version, action, length = proto_preamble
    # read in the expected message
    return version, action, recv_nbytes(sock, length)


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

