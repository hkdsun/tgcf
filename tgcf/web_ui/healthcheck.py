import http.server
import socketserver
import json
import threading
import os
import psutil

class HealthCheck:
    def __init__(self, json_file, port=8504):
        self.json_file = json_file
        self.port = port
        self.server_thread = None
        self.stop_event = threading.Event()

    def start(self):
        self.server_thread = threading.Thread(target=self._run_server)
        self.server_thread.start()

    def stop(self):
        self.stop_event.set()
        if self.server_thread:
            self.server_thread.join()

    def _run_server(self):
        handler = self._make_handler()
        with socketserver.TCPServer(("", self.port), handler) as httpd:
            print(f"Health check server serving at port {self.port}")
            while not self.stop_event.is_set():
                httpd.handle_request()

    def _make_handler(self):
        server = self
        class MyHandler(http.server.SimpleHTTPRequestHandler):
            def pidCheck(self):
                if not os.path.exists(server.json_file):
                    self.send_error(500, 'JSON file does not exist')
                else:
                    with open(server.json_file, 'r') as f:
                        data = json.load(f)
                        pid = data.get('pid', None)
                        if pid is None:
                            self.send_error(500, 'Pid is nil')
                            return

                        try:
                            pid = int(pid)
                        except ValueError:
                            self.send_error(500, 'Pid is non-int')
                            return

                        if pid == 0:
                            self.send_error(500, 'Pid is 0')
                        else:
                            if not psutil.pid_exists(pid):
                                self.send_error(500, 'Pid is not a running process')
                                return
                            
                            self.send_response(200)
                            self.send_header('Content-type', 'text/plain')
                            self.end_headers()
                            self.wfile.write(str(pid).encode())                            

            def do_GET(self):
                if self.path == '/pid':
                    self.pidCheck()
                else:
                    super().do_GET()
        return MyHandler
