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
from scipy.linalg import sqrtm
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

def get_kraus_operators(input_props, internal_props):
    """
    Construct the Kraus operators
    """
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
    kraus_operators = []
    kraus_operators.append(
        np.kron(GX,op_rais)
    )
    kraus_operators.append(
        np.kron(XG,op_low)
    )
    kraus_operators.append(
        np.sqrt(np.eye(kraus_operators[0].shape[0])- sum([k.conj().T@k for k in kraus_operators]))
    )

    kraus_indices = [internal_props.uuid, input_props.uuid]
    return kraus_operators, kraus_indices

def get_kraus_operators_big(input_props, internal_props):
    """
    Construct the Kraus operators for the actual space
    """
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
    G = np.array([1, 0, 0])
    G = G.reshape(-1,1)

    X = np.array([0,1, 0])
    X = X.reshape(-1,1)

    XX = np.array([0,0, 1])
    XX = X.reshape(-1,1)

    G_X  = np.dot(G, X.conj().T)
    G_XX = np.dot(G, XX.conj().T)
    X_XX = np.dot(X, XX.conj().T)
    XX_X = np.dot(XX, X.conj().T)
    XX_G = np.dot(XX, G.conj().T)
    X_G  = np.dot(X, G.conj().T)

    # probability of getting from G to XX
    p1 = 0.01
    # probability of getting from X to XX
    p2 = 0.05
    kraus_operators = []
    # Raising the state
    kraus_operators.append(
        np.kron(G_X,op_rais)
    )
    kraus_operators.append(
        np.sqrt(p1)*np.kron(G_XX,op_rais@op_rais)
    )
    kraus_operators.append(
        np.sqrt(p2)*np.kron(X_XX,op_rais@op_rais)
    )
    # Lowering the state
    kraus_operators.append(
        np.kron(XX_X, op_low)
    )
    kraus_operators.append(
        np.kron(XX_G, op_low@op_low)
    )
    kraus_operators.append(
        np.kron(X_G,op_low)
    )
    kraus_operators.append(
        np.sqrt(np.eye(kraus_operators[0].shape[0])- sum([k.conj().T@k for k in kraus_operators]))
    )

    kraus_indices = [internal_props.uuid, input_props.uuid]
    return kraus_operators, kraus_indices


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

    # We create Kraus operators and Kraus operators that act on the bigger space in order to
    # Compute errors

    # We compute actual internal state
    actual_internal_state_prop = StateProp(
        state_type = "internal",
        truncation = 3
    )
    actual_internal_state = State(actual_internal_state_prop)
    original_subspace = state.get_reduced_state([internal_props])
    actual_internal_state.state = np.zeros_like(actual_internal_state.state)
    actual_internal_state.state[:original_subspace.shape[0], :original_subspace.shape[1]] = original_subspace

    # We get the copy of the input light state
    input_state_copy_prop = StateProp(
        state_type = "light",
        truncation = input_props.truncation,
        wavelength = input_props.wavelength,
        polarization = input_props.polarization
    )
    input_state_copy = State(input_state_copy_prop)
    input_state_copy.state = state.get_reduced_state([input_props])

    # We construct the whole space
    state_copy = actual_internal_state
    state_copy.merge(input_state_copy)

    # We construct the kraus operators for the given state and the copy state
    kraus_operators, kraus_indices = get_kraus_operators(input_props, internal_props)
    kraus_operators_copy, kraus_indices_copy = get_kraus_operators_big(
        input_state_copy_prop, actual_internal_state_prop)


    # Apply kraus operators to the given state and the constructed copy state
    state.apply_kraus_operators(
        kraus_operators,
        state.get_all_props(kraus_indices))

    state_copy.apply_kraus_operators(
        kraus_operators_copy, state_copy.get_all_props(kraus_indices_copy)
    )

    # Get the reduced states or simulated and actual state
    reduced_state_copy = state_copy.get_reduced_state([actual_internal_state_prop])
    state = state.get_reduced_state([internal_props])
    enlarged_state = np.zeros_like(reduced_state_copy)
    enlarged_state[:state.shape[0],:state.shape[1]] = state

    fidelity = np.abs(np.trace(
        sqrtm(
            sqrtm(reduced_state_copy) @ enlarged_state @ sqrtm(reduced_state_copy)
        )
    ))
    fidelity = fidelity**2

    # decide on retriggering possibility and time
    retrigger = False
    if state[0][0] != 1:
        retrigger = True

    error = 1-fidelity

    # Construct message
    return {
        "msg_type": "channel_query_response",
        "kraus_operators": [numpy_to_json(x) for x in kraus_operators],
        "kraus_state_indices": kraus_indices,
        "error": float(error),
        "retrigger": retrigger,
        "retrigger_time": 1,  # Should retrigger in one second
        "operation_time": 1e-10
    }


@qsi.on_message("terminate")
def terminate(msg):
    qsi.terminate()

qsi.run()
time.sleep(1)


