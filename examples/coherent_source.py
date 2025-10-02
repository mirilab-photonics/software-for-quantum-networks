"""
Coherent Source example
----------------------------
It produces coherent state in a mode, the mode needs to be given on port 'input'
"""
from qsi.qsi import QSI
from qsi.helpers import numpy_to_json, pretty_print_dict
from qsi.state import State, StateProp
import time
import numpy as np
import uuid
import scipy.linalg as la
from scipy.special import factorial

# Initiate the QSI object instance
qsi = QSI()

# Store parameters
ALPHA = None

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
    Coherent Source
    Expects one praameter alpha, which has to be of complex type
    """
    return {
        "msg_type": "param_query_response",
        "params" : {
            "alpha": "complex",
            "wavelength": "number",
            "bandwidth": "number",
        }
    }

@qsi.on_message("param_set")
def param_set(msg):
    global ALPHA
    params = msg["params"]
    if "alpha" in params:
        ALPHA = complex(*params["alpha"].get("value"))
    return {
        "msg_type": "param_set_response",
    }

@qsi.on_message("channel_query")
def channel_query(msg):
    global ALPHA
    state = State.from_message(msg)
    uuid = msg["ports"]["input"]
    prop = state.get_props(uuid)
    truncation = prop.truncation

    # If state is not in vacuum state, we dont operate on it
    expected_state = np.zeros_like(state.state)
    expected_state[0,0] = 1
    if np.testing.assert_array_almost_equal(
            state.state, expected_state
    ):
        return {
            "msg_type": "channel_query_response",
            "message": f"This component only acts on a vacuum state, received non_vacuum state to operate on"
        }

    if ALPHA is None:
        return {
            "msg_type": "channel_query_response",
            "message": f"Please specify the 'alpha' (displacement) value"
        }

    create = np.zeros_like(state.state)
    for n in range(1, create.shape[0]):
        create[n,n-1] = np.sqrt(n)
    destroy = np.zeros_like(state.state)
    for n in range(1, create.shape[0]):
        destroy[n-1,n] = np.sqrt(n)

    kraus_operators = [la.expm(
        ALPHA * create - np.conjugate(ALPHA) * destroy
    )]

    kraus_operators.append(
        np.sqrt(np.eye(kraus_operators[0].shape[0])- sum([k.conj().T@k for k in kraus_operators]))
    )

    # COMPUTE ERROR

    error = 1
    summation_part = 0
    for n in range(truncation):
        summation_part += np.abs(ALPHA)**(2*n)/(factorial(n))

    error -= np.exp(-np.abs(ALPHA)**2)*summation_part

    return {
        "msg_type": "channel_query_response",
        "kraus_operators": [numpy_to_json(x) for x in kraus_operators],
        "kraus_state_indices": [uuid],
        "error": error,
        "retrigger": False,
        "retrigger_time": 1e-9,
        "alpha": [ALPHA.real, ALPHA.imag]
    }

@qsi.on_message("terminate")
def terminate(msg):
    qsi.terminate()
    
qsi.run()
time.sleep(1)
