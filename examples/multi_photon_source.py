"""
Multi-photon source example
----------------------------
It produces state of multiple photons in a mode, the mode needs to be given on port 'input' 
"""
from qsi.qsi import QSI
from qsi.helpers import numpy_to_json, pretty_print_dict
from qsi.state import State, StateProp
import time
import numpy as np
import uuid

# Initiate the QSI object instance
qsi = QSI()

# Store parameters
N_PHOTONS = None

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
    Multi photon source
    Expects one the number of photons
    """
    return {
        "msg_type": "param_query_response",
        "params" : {
            "n_photons": "number",
            "wavelength": "number",
            "bandwidth": "number",
        }
    }

@qsi.on_message("param_set")
def param_set(msg):
    """
    Multi photon source requires the number of photons
    """
    global N_PHOTONS
    
    params = msg["params"]
    if "n_photons" in params:
        N_PHOTONS = int(params["n_photons"].get("value"))
    return {
        "msg_type": "param_set_response",
    }

@qsi.on_message("channel_query")
def channel_query(msg):
    global N_PHOTONS
    
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
    # Coordinator will handle correct application to the state
    operator = np.zeros((prop.truncation, prop.truncation))
    for n in range(prop.truncation-1):
        operator[n+1, n] = 1

    operator = np.linalg.matrix_power(operator, N_PHOTONS)

    # Find other operator
    other_operator = np.sqrt(np.eye(operator.shape[0]) - operator.conjugate().T @ operator)

    # Assemble the operators
    kraus_operators = [operator, other_operator]

    # Compute error
    # TODO: Add error computation
    #     -> Error should be != 0 when initial state is |n> and n+1 is the truncation 
    error = 0

    return {
        "msg_type": "channel_query_response",
        "kraus_operators": [numpy_to_json(x) for x in kraus_operators],
        "kraus_state_indices": [uuid],
        "error": 0,
        "retrigger": False,
        "retrigger_time": 0
    }

@qsi.on_message("terminate")
def terminate(msg):
    qsi.terminate()
    
qsi.run()
time.sleep(1)
