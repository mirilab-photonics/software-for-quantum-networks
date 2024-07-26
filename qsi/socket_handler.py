"""
Socket Handler Used by Coordinator and Module
"""
import json
from jsonschema import validate
import socket
import struct
import threading
import time

from qsi.messages import SCHEMAS


class SocketHandler:
    def __init__(self, listening_port: int):
        self.listening_port = listening_port
        self.server = None
        self.should_terminate = False
        self.response_message = None
        self.server_socket = None
    
    def router(self, message):
        """
        Router routes the messages, needs to be implemented for
        module and coordinator separately
        """
        raise NotImplementedError()

    def start_server(self, port: int):
        self.server = threading.Thread(target=self.handle_connections, args=(self.listening_port,))
        self.server.start()

    def handle_connections(self, port: int):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            self.server_socket = s
            s.bind(('localhost', port))
            s.listen()
            s.settimeout(1)
            while not self.should_terminate:
                try:
                    conn, addr = s.accept()
                except socket.timeout:
                    continue
                except OSError as e:
                    # Handle the bad file descriptor error
                    if self.should_terminate:
                        break
                    else:
                        raise e
                with conn:
                    while True:
                        length_data = self.recvall(conn, 4)
                        if not length_data:
                            break
                        message_length = struct.unpack('!I', length_data)[0]
                        data = self.recvall(conn, message_length)
                        
                        if not data:
                            break
                        message = data.decode()
                        message = json.loads(message)
                        self.response_message = message
                        self.router(message)

    def recvall(self, conn, n):
        """
        Helper function to receive exactly n bytes from the socket
        """
        data = bytearray()
        while len(data) < n:
            packet = conn.recv(n-len(data))
            if not packet:
                return None
            data.extend(packet)
        return data

    def terminate(self):
        self.should_terminate = True
        self.server.join()

    def retry_connection(self, port, json_data, retries=5, delay=2):
        for attempt in range(retries):
            try:
                self.send_to(port, json_data)
                return
            except ConnectionRefusedError:
                time.sleep(delay)


    def send_to(self, port:int, message: dict):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('localhost', port))
            message["sent_from"] = int(self.listening_port)
            validate(instance=message, schema=SCHEMAS[message["msg_type"]])
            json_data = json.dumps(message)
            message = struct.pack('!I', len(json_data)) + json_data.encode('utf-8')
            s.sendall(message)
