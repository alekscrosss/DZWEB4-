import json
import mimetypes
import os
import socket
import threading
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs

# Define static and HTML file directories
HTML_FILES = {
    "/": "index.html",
    "/message": "message.html",
}
STATIC_FILES = {
    "/style.css": "style.css",
    "/logo.png": "logo.png",
}

DATA_STORE = os.getenv('DATA_STORE', 'storage/data.json')

# Ensure storage directory exists
storage_path = os.path.dirname(DATA_STORE)
if not os.path.exists(storage_path):
    os.makedirs(storage_path, exist_ok=True)

# Ensure data.json exists
if not os.path.isfile(DATA_STORE):
    with open(DATA_STORE, 'w') as file:
        file.write("{}")


class CustomHTTPRequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        # Handle static files
        if self.path in STATIC_FILES:
            file_path = STATIC_FILES[self.path]
            self.handle_file_request(file_path)
        # Handle HTML files
        elif self.path in HTML_FILES:
            file_path = HTML_FILES[self.path]
            self.handle_file_request(file_path)
        else:
            self.send_error(404, 'File Not Found')

    def do_POST(self):
        if self.path == "/message":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            form_data = parse_qs(post_data.decode('utf-8'))
            # Send form data to socket server
            send_to_socket_server(form_data)
            # Redirect to the main page
            self.send_response(302)
            self.send_header('Location', '/')
            self.end_headers()
        else:
            self.send_error(404, 'File Not Found')

    def handle_file_request(self, file_path):
        try:
            with open(file_path, 'rb') as file:
                self.send_response(200)
                mimetype, _ = mimetypes.guess_type(file_path)
                self.send_header('Content-type', mimetype)
                self.end_headers()
                self.wfile.write(file.read())
        except Exception as e:
            self.send_error(404, f'File Not Found: {e}')


def send_to_socket_server(form_data):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        # Connect to the socket server
        s.connect(('localhost', 5000))
        # Send data
        s.sendall(json.dumps(form_data).encode('utf-8'))


def run_socket_server():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server_socket:
        server_socket.bind(('localhost', 5000))
        while True:
            data, addr = server_socket.recvfrom(1024)
            process_received_data(data.decode('utf-8'))


def process_received_data(data):
    try:
        data_dict = json.loads(data)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        # Check if the storage directory exists, create if it doesn't
        os.makedirs(os.path.dirname(DATA_STORE), exist_ok=True)
        with open(DATA_STORE, 'a+') as file:
            # Load existing data and append new data
            file.seek(0)
            existing_data = file.read()
            file_data = json.loads(existing_data) if existing_data else {}
            file_data[timestamp] = data_dict
            file.seek(0)
            json.dump(file_data, file, indent=2)
    except Exception as e:
        print(f'Error processing data: {e}')


def run():
    server_address = ('', 3000)
    httpd = HTTPServer(server_address, CustomHTTPRequestHandler)
    http_thread = threading.Thread(target=httpd.serve_forever)
    socket_thread = threading.Thread(target=run_socket_server)
    http_thread.start()
    socket_thread.start()
    http_thread.join()
    socket_thread.join()


if __name__ == '__main__':
    run()
