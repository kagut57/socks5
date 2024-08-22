import socket
import struct
import threading
import os

def handle_client(client_socket):
    try:
        # Peek at the first byte without removing it from the buffer
        first_byte = client_socket.recv(1, socket.MSG_PEEK)
        if not first_byte:
            raise Exception("Empty request received")

        if first_byte[0] == 0x05:  # SOCKS5
            handle_socks5(client_socket)
        else:  # Assume HTTP
            handle_http(client_socket)

    except Exception as e:
        print(f"Error handling client: {e}")
    finally:
        client_socket.close()

def handle_socks5(client_socket):
    # SOCKS5 greeting
    greeting = client_socket.recv(262)
    print(f"Received SOCKS5 greeting: {greeting.hex()}")
    
    if len(greeting) < 2 or greeting[0] != 0x05:
        raise Exception(f"Invalid SOCKS5 greeting")
    
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

    print(f"SOCKS5: Connecting to: {target_addr}:{target_port}")

    # Connect to the target server
    target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    target_socket.connect((target_addr, target_port))
    bind_address = target_socket.getsockname()
    addr = struct.unpack("!I", socket.inet_aton(bind_address[0]))[0]
    port = bind_address[1]

    # Send connection response
    client_socket.sendall(struct.pack("!BBBBIH", 5, 0, 0, 1, addr, port))

    print(f"SOCKS5: Connected to target. Starting data forwarding.")

    # Start forwarding data
    forward_data(client_socket, target_socket)

def handle_http(client_socket):
    request = b""
    while b"\r\n\r\n" not in request:
        chunk = client_socket.recv(4096)
        if not chunk:
            break
        request += chunk

    print(f"Received HTTP request: {request}")
    
    # Parse the CONNECT request
    lines = request.split(b"\r\n")
    if not lines:
        raise Exception("Empty HTTP request")
    
    first_line = lines[0].decode('ascii')
    method, address, _ = first_line.split(' ')
    
    if method != "CONNECT":
        raise Exception(f"Unsupported HTTP method: {method}")
    
    host, port = address.split(':')
    port = int(port)

    print(f"HTTP: Connecting to: {host}:{port}")

    # Connect to the target server
    target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    target_socket.connect((host, port))

    # Send 200 Connection established
    client_socket.sendall(b"HTTP/1.1 200 Connection established\r\n\r\n")

    print(f"HTTP: Connected to target. Starting data forwarding.")

    # Start forwarding data
    forward_data(client_socket, target_socket)

def forward_data(client_socket, target_socket):
    client_to_target = threading.Thread(target=forward, args=(client_socket, target_socket))
    target_to_client = threading.Thread(target=forward, args=(target_socket, client_socket))
    client_to_target.start()
    target_to_client.start()
    client_to_target.join()
    target_to_client.join()

def forward(source, destination):
    try:
        while True:
            data = source.recv(4096)
            if not data:
                break
            destination.sendall(data)
    except Exception as e:
        print(f"Error forwarding data: {e}")
    finally:
        source.close()
        destination.close()

def main():
    port = int(os.environ.get('PORT', 80))
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', port))
    server.listen(5)

    print(f"Proxy server is running on 0.0.0.0:{port}")

    while True:
        client_socket, addr = server.accept()
        print(f"Accepted connection from {addr[0]}:{addr[1]}")
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()
        print(f"Started handler thread for {addr[0]}:{addr[1]}")

if __name__ == "__main__":
    main()
