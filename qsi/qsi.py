import argparse
import socket
import json
import threading
import struct
import sys

from qsi.socket_handler import SocketHandler


class QSI(SocketHandler):
    """
    QSI handles the communication with the coordinator process.
    """

    def __init__(self):
        parser = argparse.ArgumentParser(description="Port Handler")
        parser.add_argument('module_port', type=int, help="Module port number")
        parser.add_argument('coordinator_port', type=int,
                            help="Coordinator port number")
        args = parser.parse_args()
        self.coordinator_port = args.coordinator_port
        self.module_port = args.module_port
        super().__init__(self.module_port)
        self.server = None
        self.message_handlers = {}

    def run(self):
        """
        Start the server for communication with the Coordinator.

        This method initializes and starts the server, listening for
        incoming messages on the specified module port. It sets up the
        server to handle communication and interaction with the
        Coordinator, facilitating the exchange of messages.

        The server begins running and waits for messages on the
        designated `module_port`.
        """
        self.start_server(self.module_port)

    def on_message(self, msg_type: str):
        """
        Decorator for registering message handlers.

        This method registers a decorated function as a handler for a specific
        type of message, identified by `msg_type`. The decorated function must
        return a valid dictionary representing the message, which will be sent
        to the coordinator.

        Args:
            msg_type (str): The type of message that the decorated function
                            should handle.

        Returns:
            Callable: A decorator that registers the function in the message
                      handlers dictionary.

        Usage:
            @on_message('example_type')
            def handle_example(msg):
                # Process the message and return a response dictionary
                return {'response': 'example_response'}
        """
        def decorator(func):
            self.message_handlers[msg_type] = func
            return func
        return decorator

    def _router(self, message: dict):
        """
        Route incoming messages to the appropriate handler.

        This private method processes incoming messages by routing them to the
        appropriate handler function based on the message type. The handler
        function is retrieved from the `message_handlers` dictionary using the
        `"msg_type"` key from the message.

        If the handler function returns a response, this response is sent to
        the coordinator via the `send_to` method.

        Args:
            message (dict): A dictionary containing the message data, which
                            must include a `"msg_type"` key indicating the
                            type of the message.

        Raises:
            KeyError: If there is no handler registered for the given `msg_type`.
        """
        response = self.message_handlers[message["msg_type"]](message)
        if response is not None:
            self.send_to(self.coordinator_port, response)

    def terminate(self):
        """
        Terminate the server.

        This method sends a termination response message to the coordinator and then
        shuts down the server. The termination response indicates that the server is
        about to close.

        The method sends a dictionary with the message type `"terminate_response"` to
        the coordinator port and then exits the program with a status code of 0,
        indicating a normal shutdown.
        """
        response = {"msg_type": "terminate_response"}
        self.send_to(self.coordinator_port, response)
        sys.exit(0)
