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
    print(msg)

    # Get the uuid of the given input state
    input_uuid = msg["ports"]["input"]
    input_props = state.get_props(input_uuid)
    internal_props = state.get_props(uid)


    # Figure out the dimensions of the operator
    dims = input_props.truncation + internal_props.truncation

    if not input_props.state_type == "light":
        raise WrongStateTypeException(f"Expected Light input type, received {input_props.state_type}")

    # Construct lowering operator for the input state
    op_low = np.zeros((input_props.truncation, input_props.truncation),dtype=complex)
    for n in range(1, input_props.truncation):
        n1 = np.array([0 for x in range(input_props.truncation)])
        n1[n-1] = 1
        n1 = n1.reshape(-1,1)
        n2 = np.array([0 for x in range(input_props.truncation)])
        n2[n] = 1
        n2 = n2.reshape(1,-1)
        op_low += np.dot(n1,n2)

    # Construct raising operator for the input state
    op_rais = np.zeros((input_props.truncation, input_props.truncation),dtype=complex)
    for n in range(1, input_props.truncation):
        n1 = np.array([0 for x in range(input_props.truncation)])
        n1[n] = 1
        n1 = n1.reshape(-1,1)
        n2 = np.array([0 for x in range(input_props.truncation)])
        n2[n-1] = 1
        n2 = n2.reshape(1,-1)
        op_rais += np.dot(n1,n2)
        

    # Construct the Kraus operators
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

    # Compute error
    error = 0

    # Construct message
    return {
        "msg_type": "channel_query_response",
        "kraus_operators": [numpy_to_json(x) for x in kraus_operators],
        "error": 0,
        "retrigger": True,
        "retrigger_time": 1,  # Should retrigger in one second
        "operation_time": 1e-10
    }


@qsi.on_message("terminate")
def terminate(msg):
    qsi.terminate()

qsi.run()
time.sleep(1)

class WrongStateTypeException(Exception):
    pass
