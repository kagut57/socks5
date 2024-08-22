import socket
import threading
import os
import ssl
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def handle_client(client_socket):
    try:
        request = b""
        while b"\r\n\r\n" not in request:
            chunk = client_socket.recv(4096)
            if not chunk:
                logging.info("Empty chunk received, closing connection")
                return
            request += chunk

        logging.info(f"Received request:\n{request.decode('utf-8', 'ignore')}")

        # Parse the request
        lines = request.split(b"\r\n")
        if not lines:
            raise Exception("Empty request")

        first_line = lines[0].decode('ascii')
        method, path, version = first_line.split(' ')

        if method in ["HEAD", "GET"]:
            # Respond to HEAD and GET requests
            response = "HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nOK"
            client_socket.sendall(response.encode())
            logging.info(f"Responded to {method} request with 200 OK")
            return

        if method != "CONNECT":
            raise Exception(f"Unsupported method: {method}")

        host, port = path.split(':')
        port = int(port)

        logging.info(f"Connecting to target server {host}:{port}")

        # Connect to the target server with SSL/TLS if required
        context = ssl.create_default_context()
        target_socket = context.wrap_socket(
            socket.create_connection((host, port)),
            server_hostname=host
        )

        # Send 200 Connection established
        response = f"{version} 200 Connection established\r\n\r\n"
        client_socket.sendall(response.encode())

        logging.info(f"Connection established with target. Starting data forwarding.")

        # Start forwarding data
        forward_data(client_socket, target_socket)

    except Exception as e:
        logging.error(f"Error handling client: {e}")
        # Send error response to client
        error_response = "HTTP/1.1 500 Internal Server Error\r\n\r\n"
        client_socket.sendall(error_response.encode())
    finally:
        client_socket.close()

def forward_data(client_socket, target_socket):
    client_to_target = threading.Thread(target=forward, args=(client_socket, target_socket, "client -> target"))
    target_to_client = threading.Thread(target=forward, args=(target_socket, client_socket, "target -> client"))
    client_to_target.start()
    target_to_client.start()
    client_to_target.join()
    target_to_client.join()

def forward(source, destination, direction):
    try:
        while True:
            data = source.recv(4096)
            if not data:
                logging.info(f"No more data to forward {direction}")
                break
            logging.debug(f"Forwarding data {direction}: {len(data)} bytes")
            destination.sendall(data)
    except Exception as e:
        logging.error(f"Error forwarding data {direction}: {e}")
    finally:
        source.close()
        destination.close()

def main():
    port = int(os.environ.get('PORT', 10000))
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', port))
    server.listen(5)

    logging.info(f"HTTP proxy server is running on 0.0.0.0:{port}")

    while True:
        client_socket, addr = server.accept()
        logging.info(f"Accepted connection from {addr[0]}:{addr[1]}")
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()
        logging.info(f"Started handler thread for {addr[0]}:{addr[1]}")

if __name__ == "__main__":
    main()
