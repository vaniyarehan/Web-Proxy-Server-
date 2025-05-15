This project is a basic HTTP proxy server implemented in Python using sockets and process forking. It forwards HTTP GET requests from clients to destination servers and relays the response back to the client.
- `proxyServer.py` – Main Python script that runs the proxy server.

- Parses HTTP GET requests.
- Forwards requests to the destination server.
- Returns the response to the client.
- Handles multiple clients using `os.fork()`.
- Basic error handling for:
  - 400 Bad Request
  - 501 Not Implemented
  - 502 Bad Gateway
1. The proxy listens on a specified port.
2. When a client connects and sends an HTTP GET request, the proxy:
   - Parses the request.
   - Extracts the host, port, and path.
   - Forwards the request to the target server.
   - Relays the response back to the client.

- Python (can use C/C++ as well)
- Unix/Linux, I have implemented using Linux

to run the file on bash:
python proxyServer.py <port>
