import json
import pathlib
import socket
import threading
import urllib.parse
import mimetypes

from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer



UDP_IP = "127.0.0.1"
UDP_PORT = 5000


class HTTPHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == '/':
            self.send_html_file('front-init/index.html')
        elif pr_url.path == '/message':
            self.send_html_file('front-init/message.html')
        else:
            file_path = pathlib.Path().joinpath('front-init', pr_url.path.lstrip('/'))
            if file_path.exists():
                self.send_static(file_path)
            else:
                self.send_html_file('front-init/error.html', 404)

    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        data_parse = urllib.parse.unquote_plus(data.decode('utf-8'))
        data_dict = {key: value for key, value in [element.split('=') for element in data_parse.split('&')]}

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        data_to_send = {
            current_time: {
                "username": data_dict['username'],
                "message": data_dict['message']
            }
        }

        send_data_to_socket_server(data_to_send)

        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        with open(filename, 'rb') as file:
            self.wfile.write(file.read())

    def send_static(self, file_path):
        self.send_response(200)
        mt = mimetypes.guess_type(str(file_path))
        if mt:
            self.send_header('Content-type', mt[0])
        else:
            self.send_header('Content-type', 'text/plain')
        self.end_headers()
        with open(file_path, 'rb') as file:
            self.wfile.write(file.read())


def send_data_to_socket_server(data):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    message = json.dumps(data).encode('utf-8')
    sock.sendto(message, (UDP_IP, UDP_PORT))
    sock.close()


def run_http_server(server_class=HTTPServer, handler_class=HTTPHandler):
    server_adrees = ('', 3000)
    http = server_class(server_adrees, handler_class)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


def run_socket_server(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server = ip, port
    sock.bind(server)

    try:
        while True:
            data, client = sock.recvfrom(1024)
            data_dict = json.loads(data.decode('utf-8'))
            print(data_dict)
            with open('front-init/storage/data.json', 'a') as file:
                json.dump(data_dict, file, indent=4, ensure_ascii=False)
                file.write('\n')

            sock.sendto(data, client)

    except KeyboardInterrupt:
        sock.close()


if __name__ == '__main__':
    threading.Thread(target=run_http_server).start()
    threading.Thread(target=run_socket_server, args=(UDP_IP, UDP_PORT)).start()
