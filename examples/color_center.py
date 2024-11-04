"""
Color Centre Example
--------------------
Color Centre can store quantum state encoded with classical system.
In practice the device should be more detailed. This is just an example
on how such device should be implemented in the scope of the special issue.
"""

from qsi.qsi import QSI
from qsi.helpers import numpy_to_json, pretty_print_dict
from qsi.state import State, StateProp

import uuid
import numpy as np
from dataclasses import dataclass

"""
Example implementation for the classical signal which is
consumed by this component. This example keyboard can only
interact with signal which is enveloped in Gaussian profile
"""
@dataclass
class ClassicalSignal:
    b_amplitude: float
    frequency: float
    phase: float
    width: float

"""
Implementation of the interaction interface
 """
if __name__ == "__main__":
    qsi = QSI()
    state_uuid = uuid.uuid4()
    previous_time = 0

    @qsi.on_message("state_init")
    def state_init(msg):
        state = State(StateProp(
            state_type="internal",
            truncation=2,
            uuid=state_uuid
            ))
        return {
            "msg_type": "state_init_response",
            "states": [state.to_message()]
        }

    @qsi.on_message("param_query")
    def param_query(msg):
        """
        This component requires the following parameters
        - B0: magnetic field
        - T: temperature
        """
        return {
            "msg_type": "param_query_response",
            "params": {
                "b0": "number",
                "temp": "number",
                }
            }

    @qsi.on_message("param_set")
    def param_sest(msg):
        global B0
        global T
        params = msg["params"]
        if "b0" in params:
            B0 = float(params["b0"]["value"])
        if "temp" in params:
            T = float(params["temp"]["value"])
        return {
            "msg_type": "param_set_response"
            }

    @qsi.on_message("channel_query")
    def channel_query(msg):
        global B0
        global T
        global previous_time
        if B0 is None or T is None:
            return {
                "msg_type": "channel_query_response",
                "message": "Field {b0} or temperature {temp} was not given"
                }
        state = State.from_message(msg)

        try:
            signal = ClassicalSignal(**msg["signals"][0])
        except Exception as e:
            return {
                "msg_type": "channel_query_response",
                "message": f"Signal parameters could not be read, {e}"
                }
        """
        Here the user should construct the Kraus operators
        """
        operator_one = np.zeros((2,2))
        operator_one[1,0] = 1

        operator_two = np.zeros((2,2))
        operator_two[1,1] = 1

        operators = [operator_one, operator_two]
        """
        One could also define the operator taking into account
        the time difference between previous interaction and
        this one
        """
        if previous_time is None:
            previous_time = 0
        time_delta = float(msg["time"]) - previous_time
        # operators = generate_operators(time_delta, *args)

        return {
            "msg_type" : "channel_query_response",
            "kraus_operators" : [ numpy_to_json(op) for op in operators],
            "kraus_state_indices" : [str(state_uuid)],
            "error" : 0,
            "operation_time" : signal.width,
            "retrigger" : False
            }

    qsi.run()
