"""
Simple Memory with error
-----------------
Simulates a memory, where a memory has 3 states: |G>, |X>, |XX>; (ground level,
exciton level, biexciton level). This memory is unlikely to be excited to the state |XX>,
so in the simulation we neglect the state, which produces some error.
"""
from qsi.qsi import QSI
from qsi.helpers import numpy_to_json, pretty_print_dict
from qsi.state import State, StateProp
import time
import numpy as np
import uuid

qsi = QSI()
uid = str(uuid.uuid4())

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

    # Get the uuid of the given input state
    input_uuid = msg["ports"]["input"]
    input_props = state.get_props(input_uuid)
    internal_props = state.get_props(uid)


    # Figure out the dimensions of the operator
    dims = input_props.truncation + internal_props.truncation

    if not input_props.state_type == "light":
        raise WrongStateTypeException(f"Expected Light input type, received {input_props.state_type}")


    G = np.array([1, 0])
    G = G.reshape(-1,1)

    X = np.array([0,1])
    X = X.reshape(-1,1)

    GX = np.dot(G, X.conj().T)
    XG = np.dot(X, G.conj().T)

    # Computing absorption operator
    kraus_operators = []
    kraus_operators.append(
        np.kron(GX,op_low)
    )
    kraus_operators.append(
        np.kron(XG,op_rais)
    )
    kraus_operators.append(
        np.sqrt(np.eye(kraus_operators[0].shape[0])- sum([k.conj().T@k for k in kraus_operators]))
    )

    kraus_indices = [internal_props.uuid, input_uuid]

    # Compute error
    error = 0


    # decide on retriggering possibility and time
    state.apply_kraus_operators(kraus_operators, [internal_props, input_props])
    resulting_state = state.get_reduced_state([internal_props])
    retrigger = False
    if resulting_state[0][0] != 1:
        retrigger = True
        

    # Construct message
    return {
        "msg_type": "channel_query_response",
        "kraus_operators": [numpy_to_json(x) for x in kraus_operators],
        "kraus_state_indices": kraus_indices,
        "error": 0,
        "retrigger": retrigger,
        "retrigger_time": 1,  # Should retrigger in one second
        "operation_time": 1e-10
    }


@qsi.on_message("terminate")
def terminate(msg):
    qsi.terminate()

qsi.run()
time.sleep(1)
