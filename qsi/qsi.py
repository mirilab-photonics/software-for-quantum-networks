import argparse
import socket
import json
import threading
import struct

class QSI:
    """
    QSI Class handles the communication
    """

    def __init__(self):
        parser = argparse.ArgumentParser(description="Port Handler")
        parser.add_argument('module_port', type=int, help="Module port number")
        parser.add_argument('coordinator_port',type=int, help="Coordinator port number")
        args = parser.parse_args()

        self.coordinator_port = args.coordinator_port
        self.module_port = args.module_port
        self.coordinator_port = args.coordinator_port
        self.module_port = args.module_port
        self.server = None
        self.message_handlers = {}

    def run(self):
        """
        Starts the server for communication with the Coordinator
        """
        self.start_server(self.module_port)

    def start_server(self, port):
        self.server = threading.Thread(target=self.handle_connections, args=(port,))
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

                        try:
                            message_json = json.loads(message)
                            msg_type = message_json.get("msg_type")
                            if msg_type in self.message_handlers:
                                print(f"Received message on port {port}: {msg_type}")
                                message_dict = json.dumps(message_json)
                                response_dict = self.message_handlers[msg_type](message_dict)
                                self.send_to_coordinator(response_dict)
                        except json.JSONDecodeError as e:
                            print(f"Failed to decode JSON: {e}")
                        

    def recvall(self, conn, n):
        """ Helper function to receive exactly n bytes from the socket"""
        data = bytearray()
        while len(data)<n:
            packet = conn.recv(n-len(data))
            if not packet:
                return None
            data.extend(packet)
        return data

    def send_to_coordinator(self, response_dict):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('localhost', self.coordinator_port))
            response_json = json.dumps(response_dict)
            message = struct.pack('!I', len(response_json)) + response_json.encode('utf-8')
            s.sendall(message)
            print(f"Sent the data to the coordinator: {response_dict['msg_type']}")

    def on_message(self, msg_type):
        def decorator(func):
            self.message_handlers[msg_type] = func
            return func
        return decorator

    def terminate(self):
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        print("Server terminated")
