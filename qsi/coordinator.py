"""
Coordinator
"""
import argparse
import json
import socket
import subprocess
import struct
import threading
import time


def find_empty_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))  # Bind to any available address on port 0
        return s.getsockname()[1]

def is_port_open(port, host='localhost', timeout=1.0):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        try:
            s.connect((host, port))
            return True
        except (ConnectionRefusedError, socket.timeout):
            return False
    
class ModuleReference:
    def __init__(self, module, port, coordinator_port, runtime):
        self.module = module
        self.port = port
        self.runtime = runtime
        if runtime == "python":
            command = ["python", module, str(port), str(coordinator_port)]
        print(command)
        self.process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Start threads to capture stdout and stderr
        threading.Thread(target=self._capture_output, args=(self.process.stdout, "stdout")).start()
        threading.Thread(target=self._capture_output, args=(self.process.stderr, "stderr")).start()

    def _capture_output(self, stream, stream_name):
        for line in iter(stream.readline, ''):
            print(f"[{stream_name}] {line.strip()}")
        stream.close()

class Coordinator:
    def __init__(self):
        parser = argparse.ArgumentParser(description="Coordinator arg parser")
        parser.add_argument("coordinator_port", type=int, help="Coordinator port")
        args = parser.parse_args()

        self.modules = []
        self.coordinator_port = args.coordinator_port
        self.coordinator_send_port = find_empty_port()

    def start_server(self):
        self.server = threading.Thread(target=self.handle_connections, args=(self.coordinator_port,))
        self.server.start()

    def handle_connections(self, port):
        """
        Handles connections
        """
        print("Starting server")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', port))
            s.listen()
            print(f"Listening on port {port}")
            while True:
                conn, addr = s.accept()
                with conn:
                    print(f"Connected by {addr}")
                    while True:
                        #First receive the message length
                        length_data = self.recvall(conn, 4)
                        if not length_data:
                            break
                        message_length = struct.unpack('!I', length_data)[0]

                        data = self.recvall(conn, message_length)
                        if not data:
                            break
                        message = data.decode()
                        print(message)
                        

    def recvall(self, conn, n):
        """ Helper function to receive exactly n bytes from the socket"""
        data = bytearray()
        while len(data)<n:
            packet = conn.recv(n-len(data))
            if not packet:
                return None
            data.extend(packet)
        return data

    def run(self):
        self.start_server()
        for (module, port) in self.modules:
            msg = {"msg_type": "state_init"}
            json_data = json.dumps(msg)
            self.retry_connection(port, json_data)

    def retry_connection(self, port, json_data, retries=5, delay=2):
        for attempt in range(retries):
            try:
                self.send_from_coordinator_port(port, json_data)
                print(f"Successfully connected and sent data to port {port}")
                return
            except ConnectionRefusedError:
                print(f"Connection refused on port {port}, retrying...")
                time.sleep(delay)
        print(f"Failed to connect to port {port} after {retries} attempts")

    def send_from_coordinator_port(self, port, json_data):
        source_port = self.coordinator_send_port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', source_port))
            s.connect(('localhost', port))
            message = struct.pack('!I', len(json_data)) + json_data.encode('utf-8')
            s.sendall(message)
            print(f"Sent data from port {source_port} to port {port}")

    def register_componnet(self, module, port=None, runtime="python"):
        if port is None:
            port = find_empty_port()
        mr = ModuleReference(module, port, self.coordinator_port, runtime)
        self.modules.append((module, port))
        return module
    
