import socket
import struct
import sys
import os

def main():
    multicast_group = os.environ['MULTICAST_GROUP']
    server_address = ('', int(os.environ['SOCK_PORT']))
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(server_address)
    
    group = socket.inet_aton(multicast_group)
    mreq = struct.pack('4sL', group, socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    
    node_name = os.environ['NODE_NAME'].split('.')[0]
    
    while True:
        sys.stdout.write('waiting to recieve message \n')
        data, address = sock.recvfrom(1024)
    
        sys.stdout.write(f'recieved {len(data)} bytes from {address} --> {data.decode()} \n')
    
        sys.stdout.write(f'sending acknowledgment to {address} \n')
        sock.sendto(node_name.encode(), address)

if __name__ == "__main__":
    main()