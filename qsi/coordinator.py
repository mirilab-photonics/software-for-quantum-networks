"""
Coordinator
"""
import argparse
import json
import socket
import struct
import threading
import time

from qsi.socket_handler import SocketHandler
from qsi.module_reference import ModuleReference


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
    
class Coordinator(SocketHandler):
    def __init__(self):
        parser = argparse.ArgumentParser(description="Coordinator arg parser")
        parser.add_argument("coordinator_port", type=int, help="Coordinator port")
        args = parser.parse_args()
        super().__init__(listening_port=args.coordinator_port)
        self.modules = []
        self.coordinator_port = args.coordinator_port
        self.condition = threading.Condition()
        self.response_received = True

    def run(self):
        self.start_server(self.coordinator_port)
        for (module, port, mr) in self.modules:
            msg = {"msg_type": "param_query"}
            self.retry_connection(port, msg)

    def register_componnet(self, module, port=None, runtime="python"):
        if port is None:
            port = find_empty_port()
        mr = ModuleReference(module, port, self.coordinator_port, runtime, self)
        self.modules.append((module, port, mr))
        return mr

    def router(self, message):
        print(message)
        mr = self.get_module_reference(message["sent_from"])[2]
        match message["msg_type"]:
            case "param_query_response":
                if "params" in message.keys():
                    mr.notify_params(message["params"])

        with self.condition:
            self.response_received = True
            self.condition.notify()

    def send_to(self, port, message):
        with self.condition:
            while not self.response_received:
                self.condition.wait()
            self.response_received = False
            super().send_to(port, message)

    def retry_connection(self, port, json_data, retries=5, delay=2):
        for attempt in range(retries):
            try:
                print("Sending to")
                self.send_to(port, json_data)
                print(f"Successfully connected and sent data to port {port}")
                return
            except ConnectionRefusedError:
                print(f"Connection refused on port {port}, retrying...")
                time.sleep(delay)
                self.response_received = True
        print(f"Failed to connect to port {port} after {retries} attempts")


    def get_module_reference(self, sent_from):
        return [x for x in self.modules if x[1] == sent_from][0]

    def state_init(self):
        for (module, port, mr) in self.modules:
            msg = {"msg_type": "state_init"}
            self.retry_connection(port, msg)

    def send_and_return_response(self, port, message):
        with self.condition:
            self.send_to(port, message)
            while not self.response_received:
                self.condition.wait()
            return self.response_message

    def terminate(self):
        """
        Terminates all modules and joins the processes
        """
        for (module, port, mr) in self.modules:
            message = {"msg_type": "terminate"}
            self.send_and_return_response(port, message)
            mr.terminate()

        self.should_terminate = True
        if self.server_socket:
            self.server_socket.close()  # This will unblock the accept call
        if self.server:
            self.server.join()


class FalseInternalStateNumber(Exception):
    pass
