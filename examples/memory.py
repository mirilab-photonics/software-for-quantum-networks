"""
Simple Memory example
----------------------------
It stores a photon in memory.
"""
from qsi.qsi import QSI
from qsi.helpers import numpy_to_json, pretty_print_dict
from qsi.state import State, StateProp
import time
import numpy as np
import uuid

qsi = QSI()
uid = uuid.uuid4

@qsi.on_message("param_query")
def param_query(msg):
    """
    Single Photon Source
    declares no parameters
    """
    return {
        "msg_type": "param_query_response",
    }


@qsi.on_message("state_init")
def state_init(msg):
    """
    Memory has internal state, which is declared here
    """
    state = State(StateProp(
        state_type="internal",
        truncation=2,
        uuid=uid
    ))

    # We initiate a quanutm state in ground state
    msg = {
        "msg_type": "state_init_response",
        "states": [state.to_message()]
    }
    return msg

@qsi.on_message("channel_query")
def channel_query(msg):
    state = State.from_message(msg)
    print(msg)

    # Get the uuid of the given input state
    input_uuid = msg["ports"]["input"]
    input_props = state.get_props(input_uuid)

    if input_props.state_type not "Light":
        raise WrongStateTypeException("Expected Light input type, received {input_props.state_type}")

    # Construct lowering operator for the input state
    op = np.zeros((input_props.truncation, input_prop.truncation),dtype=np.complex)
    for n in range(props.truncation -1):
        operator(n, n+1) = 1


    # Construct the Kraus operators
    G = np.array([1, 0])
    G = G.reshape(-1,1)

    X = np.array([0,1])
    X = X.reshape(-1,1)

    # Compute Error

    # Construct message

    raise Exception("DEBUG")
    pass

@qsi.on_message("terminate")
def terminate(msg):
    qsi.terminate()

qsi.run()
time.sleep(1)

class WrongStateTypeException(Exception):
    pass
