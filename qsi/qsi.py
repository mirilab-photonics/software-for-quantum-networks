import argparse
import socket
import json
import threading
import struct
import sys

from qsi.socket_handler import SocketHandler

class QSI(SocketHandler):
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
        super().__init__(self.module_port)
        self.server = None
        self.message_handlers = {}

    def run(self):
        """
        Starts the server for communication with the Coordinator
        """
        self.start_server(self.module_port)

    def on_message(self, msg_type: str):
        def decorator(func):
            self.message_handlers[msg_type] = func
            return func
        return decorator

    def router(self, message: dict):
        print(self.message_handlers)
        response = self.message_handlers[message["msg_type"]](message)
        if response is not None:
            self.send_to(self.coordinator_port, response)
            

    def terminate(self):
        response = {"msg_type":"terminate_response"}
        self.send_to(self.coordinator_port, response)
        sys.exit(0)
