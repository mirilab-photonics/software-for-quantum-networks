"""
Jx coupler example
----------------------------
It models the photon probability distribution at the output of the Jx coupler
"""
from qsi.qsi import QSI
from qsi.helpers import numpy_to_json, pretty_print_dict
from qsi.state import State, StateProp
import time
import numpy as np
import uuid
import scipy.linalg as la
from scipy.special import factorial
from scipy.linalg import expm

# Initiate the QSI object instance
qsi = QSI()

# Store parameters
N_PORTS = None
LENGTH = None
REFRACTIVE_INDEX = None
C0 = 299792458  # Speed of light in vacuum 

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
    Jx coupler expects three number parameters: n_ports (integer), refractive index n (float), and length (float)
    """
    return {
        "msg_type": "param_query_response",
        "params" : {
            "n_ports": "number",
            "n": "number",
            "length": "number",
        }
    }

@qsi.on_message("param_set")
def param_set(msg):
    global N_PORTS
    global REFRACTIVE_INDEX
    global LENGTH
    params = msg["params"]
    if "length" in params:
        LENGTH = float(params["length"].get("value"))
    if "n" in params:
        REFRACTIVE_INDEX = float(params["n"].get("value"))
    if "n_ports" in params:
        N_PORTS = int(params["n_ports"].get("value"))
    return {
        "msg_type": "param_set_response",
    }

@qsi.on_message("channel_query")
def channel_query(msg):
    global N_PORTS
    global REFRACTIVE_INDEX
    global LENGTH
    global C0

    # Parse the incoming composite state
    state = State.from_message(msg)

    # Collect input uuids: allow a single uuid, a list, or a dict of ports
    ports = msg.get("ports", {})
    uuids = msg["ports"]["input"]

    # Parameter checks
    if N_PORTS is None or REFRACTIVE_INDEX is None or LENGTH is None:
        return {
            "msg_type": "channel_query_response",
            "message": "This component requires 'n_ports', 'n' (refractive index), and 'length' [m] to be set."
        }
    if len(uuids) != N_PORTS:
        return {
            "msg_type": "channel_query_response",
            "message": f"Expected {N_PORTS} input ports, received {len(uuids)}."
        }

    props = [state.get_props(u) for u in uuids]
    # Basic sanity: all light, 1550 nm, same truncation
    if any(p.state_type != "light" for p in props):
        return {
            "msg_type": "channel_query_response",
            "message": "All inputs must be light modes."
        }
    if any(p.wavelength != 1550 for p in props):
        return {
            "msg_type": "channel_query_response",
            "message": f"This component only interacts with 1550 nm modes."
        }
    d = props[0].truncation
    if any(p.truncation != d for p in props):
        return {
            "msg_type": "channel_query_response",
            "message": "All input spaces must have the same truncation."
        }

    # Build single-mode operators
    I = np.eye(d)
    adag = np.zeros((d, d))
    for i in range(d - 1):
        adag[i + 1, i ] = np.sqrt(i + 1)
    a = adag.conj().T  # annihilation

    # Build N-partite annihilation operators a_j over the tensor product
    a_partite = []
    for j in range(N_PORTS):
        opj = None
        for m in range(N_PORTS):
            block = a if m == j else I
            opj = block if opj is None else np.kron(opj, block)
        a_partite.append(opj)

    # Coupling strengths κ_j for Jx lattice
    kappas = [np.sqrt((N_PORTS - i - 1) * (i + 1)) / 2 for i in range(N_PORTS - 1)]

    # Jx Hamiltonian: sum κ_j (a_j^† a_{j+1} + h.c.)
    H = np.zeros_like(a_partite[0], dtype=complex)
    for j in range(N_PORTS - 1):
        H += kappas[j] * (a_partite[j].conj().T @ a_partite[j + 1] +
                          a_partite[j + 1].conj().T @ a_partite[j])

    # Single Kraus operator is the unitary U = exp(-i H L)
    U = expm(-1j * H * LENGTH)

    operating_time = LENGTH / (REFRACTIVE_INDEX * C0)

    return {
        "msg_type": "channel_query_response",
        "kraus_operators": [numpy_to_json(U)],
        "kraus_state_indices": uuids,   # very important: match the kron order
        "error": 0,
        "retrigger": False,
        "retrigger_time": 0,
        "operating_time": operating_time
    }


@qsi.on_message("terminate")
def terminate(msg):
    qsi.terminate()
    
qsi.run()
time.sleep(1)
