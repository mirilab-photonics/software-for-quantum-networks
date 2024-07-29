"""
Single Photon Source example
----------------------------
It produces one photon in a mode, the mode needs to be given on port 'input' 
"""
from qsi.qsi import QSI
from qsi.helpers import numpy_to_json, pretty_print_dict
from qsi.state import State, StateProp
import time
import numpy as np
import uuid

qsi = QSI()
STATE_UUIDS = []

@qsi.on_message("state_init")
def state_init(msg):
    return {
        "msg_type": "state_init_response",
        "states": [],
        "state_ids": []
    }

@qsi.on_message("param_query")
def param_query(msg):
    """
    Single Photon Source
    declares no parameters
    """
    return {
        "msg_type": "param_query_response",
        "params" : [["test", "complex"]]
    }

@qsi.on_message("param_set")
def param_set(msg):
    """
    Single photon source doesn't require any parameters
    """
    return {
        "msg_type": "param_set_response",
    }

@qsi.on_message("channel_query")
def channel_query(msg):
    state = State.from_message(msg)
    uuid = msg["ports"]["input"]
    prop = state.get_props(uuid)

    # Do not compute channel, if mode with wrong properties is given
    if prop.wavelength != 1550:
        return {
            "msg_type": "channel_query_response",
            "message": f"This component only interacts with 1550 nm modes, received {prop.wavelength}, {type(prop.wavelength)}"
        }

    # Create operator, which only acts on the designated space
    operator = np.zeros((prop.truncation, prop.truncation))
    for n in range(prop.truncation-1):
        operator[n+1, n] = 1

    # Pad Operator, so that it can act on the potential product space
    padded_operator = 1
    for p in state.state_props:
        if p.uuid == uuid:
            padded_operator = np.kron(padded_operator, operator)
        else:
            padded_operator = np.kron(padded_operator, np.eye(p.truncation))

    # Find other operator
    other_operator = np.sqrt(np.eye(padded_operator.shape[0]) - padded_operator.conjugate().T @ padded_operator)

    # Assemble the operators
    kraus_operators = [padded_operator, other_operator]

    # Compute error
    # TODO: Add error computation
    #     -> Error should be != 0 when initial state is |n> and n+1 is the truncation 
    error = 0

    return {
        "msg_type": "channel_query_response",
        "kraus_operators": [numpy_to_json(x) for x in kraus_operators],
        "error": 0,
        "retrigger": False,
        "retrigger_time": 0
    }

@qsi.on_message("terminate")
def terminate(msg):
    qsi.terminate()
    
qsi.run()
time.sleep(1)
