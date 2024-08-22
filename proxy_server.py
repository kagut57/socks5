import socket
import select
import struct
import threading

def handle_client(client_socket):
    try:
        # SOCKS5 greeting
        greeting = client_socket.recv(262)
        if not greeting or len(greeting) < 2 or greeting[0] != 0x05:
            raise Exception("Invalid SOCKS5 greeting")
        client_socket.sendall(b"\x05\x00")

        # SOCKS5 connection request
        request = client_socket.recv(4)
        if len(request) < 4:
            raise Exception("Invalid SOCKS5 request")
        version, cmd, _, address_type = struct.unpack("!BBBB", request)
        
        if address_type == 1:  # IPv4
            target_addr = socket.inet_ntoa(client_socket.recv(4))
        elif address_type == 3:  # Domain name
            domain_length = ord(client_socket.recv(1))
            target_addr = client_socket.recv(domain_length).decode('ascii')
        elif address_type == 4:  # IPv6
            target_addr = socket.inet_ntop(socket.AF_INET6, client_socket.recv(16))
        else:
            raise Exception(f"Unsupported address type: {address_type}")

        target_port = struct.unpack('!H', client_socket.recv(2))[0]

        # Connect to the target server
        target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        target_socket.connect((target_addr, target_port))
        bind_address = target_socket.getsockname()
        addr = struct.unpack("!I", socket.inet_aton(bind_address[0]))[0]
        port = bind_address[1]

        # Send connection response
        client_socket.sendall(struct.pack("!BBBBIH", 5, 0, 0, 1, addr, port))

        # Start forwarding data
        client_to_target = threading.Thread(target=forward, args=(client_socket, target_socket))
        target_to_client = threading.Thread(target=forward, args=(target_socket, client_socket))
        client_to_target.start()
        target_to_client.start()

    except Exception as e:
        print(f"Error handling client: {e}")
        client_socket.close()

def forward(source, destination):
    while True:
        try:
            data = source.recv(4096)
            if not data:
                break
            destination.sendall(data)
        except:
            break
    source.close()
    destination.close()

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', 1080))
    server.listen(5)

    print("SOCKS5 proxy server is running on 0.0.0.0:1080")

    while True:
        client_socket, addr = server.accept()
        print(f"Accepted connection from {addr[0]}:{addr[1]}")
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()

if __name__ == "__main__":
    main()
