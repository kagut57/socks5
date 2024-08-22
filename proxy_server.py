import socket
import threading
import os

def handle_client(client_socket):
    try:
        request = b""
        while b"\r\n\r\n" not in request:
            chunk = client_socket.recv(4096)
            if not chunk:
                raise Exception("Empty request received")
            request += chunk

        print(f"Received request: {request}")

        # Parse the request
        lines = request.split(b"\r\n")
        if not lines:
            raise Exception("Empty request")

        first_line = lines[0].decode('ascii')
        method, path, _ = first_line.split(' ')

        if method == "HEAD":
            # Respond to HEAD request (for Render's health check)
            response = "HTTP/1.1 200 OK\r\nContent-Length: 0\r\n\r\n"
            client_socket.sendall(response.encode())
            return

        if method != "CONNECT":
            raise Exception(f"Unsupported method: {method}")

        host, port = path.split(':')
        port = int(port)

        print(f"Connecting to: {host}:{port}")

        # Connect to the target server
        target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        target_socket.connect((host, port))

        # Send 200 Connection established
        client_socket.sendall(b"HTTP/1.1 200 Connection established\r\n\r\n")

        print(f"Connected to target. Starting data forwarding.")

        # Start forwarding data
        forward_data(client_socket, target_socket)

    except Exception as e:
        print(f"Error handling client: {e}")
    finally:
        client_socket.close()

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

    print(f"HTTP proxy server is running on 0.0.0.0:{port}")

    while True:
        client_socket, addr = server.accept()
        print(f"Accepted connection from {addr[0]}:{addr[1]}")
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()
        print(f"Started handler thread for {addr[0]}:{addr[1]}")

if __name__ == "__main__":
    main()
