import os
import socket
import sys

BUFFER_SIZE = 8192
MAX_PROCESSES = 100
current_processes = 0

def parse_request(request):
    try:
        lines = request.split("\r\n")
        if not lines:
            return None, None, None, None, 400

        first_line = lines[0].split()
        if len(first_line) < 3:
            return None, None, None, None, 400

        method, url, version = first_line
        if method != "GET":
            return None, None, None, None, 501

        if not url.startswith("http://"):
            return None, None, None, None, 400

        url = url[7:]  # Remove "http://"
        path_start = url.find('/')
        if path_start != -1:
            host_port = url[:path_start]
            path = url[path_start:]
        else:
            host_port = url
            path = "/"

        if ':' in host_port:
            host, port = host_port.split(':')
            port = int(port)
        else:
            host = host_port
            port = 80
        
        headers = {line.split(': ')[0]: line.split(': ')[1] for line in lines[1:] if ': ' in line}
        
        return host, port, path, headers, 200
    except Exception:
        return None, None, None, None, 400

def send_error_response(client_socket, status_code, message):
    response = f"HTTP/1.0 {status_code} {message}\r\nContent-Type: text/plain\r\nContent-Length: {len(message)}\r\n\r\n{message}"
    client_socket.sendall(response.encode())
    client_socket.close()

def forward_request(client_socket, request):
    host, port, path, headers, status = parse_request(request)
    
    if status == 400:
        print("[ERROR] 400 Bad Request")
        send_error_response(client_socket, 400, "Bad Request")
        return
    
    if status == 501:
        print("[ERROR] 501 Not Implemented")
        send_error_response(client_socket, 501, "Not Implemented")
        return

    try:
        print(f"[INFO] Forwarding request to {host}:{port}{path}")
        
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.connect((host, port))

        http_request = f"GET {path} HTTP/1.0\r\nHost: {host}\r\n"
        
        for header, value in headers.items():
            if header.lower() not in ["host", "connection"]:
                http_request += f"{header}: {value}\r\n"

        http_request += "Connection: close\r\n\r\n"
        server_socket.sendall(http_request.encode())

        while True:
            data = server_socket.recv(BUFFER_SIZE)
            if not data:
                break
            client_socket.sendall(data)

        server_socket.close()
        print("[INFO] Response sent back to client")
    except Exception as e:
        print("[ERROR] 502 Bad Gateway", e)
        send_error_response(client_socket, 502, "Bad Gateway")
    
    client_socket.close()

def start_proxy(port):
    global current_processes
    proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    proxy_socket.bind(("0.0.0.0", port))
    proxy_socket.listen(100)
    
    print(f"[INFO] Proxy server running on port {port}...")
    
    while True:
        if current_processes >= MAX_PROCESSES:
            print("[WARNING] Maximum process limit reached. Waiting...")
            os.wait()
            current_processes -= 1
        
        client_socket, client_addr = proxy_socket.accept()
        print(f"[INFO] New connection from {client_addr}")
        
        pid = os.fork()
        
        if pid == 0:
            proxy_socket.close()
            request = client_socket.recv(BUFFER_SIZE).decode(errors='ignore')
            print(f"[INFO] Received request:\n{request}")
            forward_request(client_socket, request)
            os._exit(0)
        
        else:
            current_processes += 1
            client_socket.close()
            
            while True:
                try:
                    pid, _ = os.waitpid(-1, os.WNOHANG)
                    if pid > 0:
                        current_processes -= 1
                    else:
                        break
                except ChildProcessError:
                    break

def main():
    if len(sys.argv) != 2:
        print("Usage: python proxy.py <port>")
        sys.exit(1)
    
    port = int(sys.argv[1])
    start_proxy(port)

if __name__ == "__main__":
    main()

