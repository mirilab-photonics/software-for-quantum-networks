"""
Simple Quantum State Handler
"""
from dataclasses import dataclass, field, asdict
import numpy as np
from typing import Literal, Optional
import uuid
import itertools

from type_enforced import Enforcer

from qsi.helpers import numpy_to_json, json_to_numpy


@dataclass
class StateProp:
    state_type: Literal["light", "internal"]
    truncation: int
    uuid: Optional[str] = field(default=None)
    wavelength: Optional[float] =field(default=None) # Wavelength in nanometers
    polarization: Optional[Literal["R", "L", "H", "V"]] = field(default=None)

    def __post_init__(self):
        if self.uuid is None:
            self.uuid = str(uuid.uuid4())
        if self.state_type == "light":
            if self.wavelength is None:
                raise ValueError("Wavelength needs to be set for light type")
            self.wavelength = float(self.wavelength)
            if self.polarization is None:
                raise ValueError("Polarization needs to be set for light type")
        if self.truncation is None:
            raise ValueError("Truncation needs to be set for all state types")
        self.truncation = int(self.truncation)
    def dict(self):
        return {k: str(v) for k, v in asdict(self).items()}


class State:
    def __init__(self, state_prop=None, empty=False):
        if not empty:
            self.state_props = [state_prop]
            self.state = np.zeros((state_prop.truncation, state_prop.truncation), dtype=complex)
            self.state[0,0] = 1
            self.dimensions = state_prop.truncation

    def join(self, other: "State"):
        self.state = np.kron(self.state, other.state)
        self.state_props.extend(other.state_props)
        self.dimensions *= other.dimensions
        other = None

    def to_message(self, port_assign=None, msg_type="channel_query"):
        message = {
            "dimensions": self.dimensions,
            "state": numpy_to_json(self.state),
            "state_props": [x.dict() for x in self.state_props]
        }
        if port_assign is not None:
            message["ports"]=port_assign
        return message
        
    @classmethod
    def from_message(cls, state_dict: dict):
        s = State(empty=True)
        s.state = json_to_numpy(state_dict["state"])
        s.state_props = [StateProp(**x) for x in state_dict["state_props"]]
        s.dimensions = state_dict["dimensions"]
        return s

    def get_index(self, uuid:str) -> int:
        ids = [x.uuid for x in self.state_props]
        return ids.index(uuid)

    def get_props(self, uuid) -> StateProp:
        return [x for x in self.state_props if x.uuid == uuid][0]

    def get_all_props(self, uuids) -> list[StateProp]:
        uuid_to_prop = {x.uuid: x for x in self.state_props}
        return [uuid_to_prop[uuid] for uuid in uuids if uuid in uuid_to_prop]

    @Enforcer
    def _reorder(self, new_prop_order:list[StateProp]):
        """
        Reorders the spaces in the product space
        """

        dims = [prop.truncation for prop in self.state_props]

        # Figuring out old and new order
        new_uuids = [p.uuid for p in new_prop_order]
        current_order = [prop.uuid for prop in self.state_props]
        remove_set = set([p.uuid for p in new_prop_order])
        new_order = [uid for uid in current_order if uid not in remove_set]
        new_order = [p.uuid for p in new_prop_order] + new_order


        indices = {}
        for uid in current_order:
            indices[uid] = {
                1: [],
                2: []
            }

        e_start = []
        counter = itertools.count(start=0)

        for i in range(2):
            for uid in current_order:
                if i == 0:
                    val = next(counter)
                    indices[uid][1] = val
                if i == 1:
                    val = next(counter)
                    indices[uid][2] = val
        
                e_start.append(val)

        e_finish = []
        for i in range(2):
            for uid in new_order:
                if i == 0:
                    val = indices[uid][1]
                else:
                    val = indices[uid][2]
                e_finish.append(val)


        # Preparing state for reordering by reshaping
        reshaped_dims = [dim for dim in dims] + [dim for dim in dims]
        self.state = self.state.reshape(reshaped_dims)

        self.state = np.einsum(self.state, e_start, e_finish)
        new_prop_order = self.get_all_props(new_order)
        self.state_props = new_prop_order
        self.state = self.state.reshape(np.prod(dims), np.prod(dims))

    @Enforcer
    def apply_kraus_operators(self, operators:list,
                              operation_spaces:list[StateProp]):
        """
        Applies a set of Kraus operators to a specified subspace of the system's state.

        This method takes a list of Kraus operators and applies them to the state of the system,
        specifically within the subspace defined by `operation_spaces`. The Kraus operators should
        correspond to these operation spaces in the given order.

        Parameters
        ----------
        operators : list
            A list of numpy arrays representing the Kraus operators. Each operator should be 
            appropriately shaped to match the dimensions of the corresponding `operation_spaces`.

        operation_spaces : list[StateProp]
            A list of `StateProp` objects defining the subspace on which the Kraus operators act.
            The order of these objects must match the order of the spaces in the Kraus operators.

        Raises
        ------
        AssertionError
            If any `StateProp` in `operation_spaces` is not present in `self.state_props`.

        Notes
        -----
        - The method reshapes the current state to a multi-dimensional array corresponding to
        the direct product space of the system's state properties.
        - The indices for contraction are carefully assigned to match the Kraus operators and 
        the state, ensuring proper application of the Kraus operators.
        - The result is stored back in the `self.state` attribute after reshaping to the original 
        matrix form.

        Example
        -------
        If `self.state_props` contains subsystems A and B, and the Kraus operators act on subsystem A,
        then `operation_spaces` should specify subsystem A, and the method will apply the Kraus
        operators to subsystem A, leaving subsystem B unchanged.
        """
        for p in operation_spaces:
            assert p in self.state_props

        state_order = [prop.uuid for prop in self.state_props]

        # First we reshape the state matrix
        dims = [p.truncation for p in self.state_props]
        reshaped_dims = [dim for dim in dims] + [dim for dim in dims]
        self.state = self.state.reshape(reshaped_dims)

        # Get the order of the spaces in the product space
        state_order = [prop.uuid for prop in self.state_props]
        operator_order = [prop.uuid for prop in operation_spaces]

        # We will keep track of the three sets of indices for each space
        indices = {}
        for uid in state_order:
            indices[uid] = {
                1: [],  # indices in first operator
                2: [],  # indices in the state
                3: []   # indices in the second operator
            }

        op_1_idcs = [] # First operator indices
        state_idcs = [] # State indices
        op_2_idcs = [] # Second operator indices
        result_idcs = [] # Resulting indices

        counter = itertools.count(start=0)

        # Assigning first operator indices
        for i in range(2):
            for idc in operator_order:
                val = next(counter)
                op_1_idcs.append(val)
                indices[idc][1].append(val)

        # Assigning state indices
        for i in range(2):
            for idc in state_order:
                if idc in operator_order and i == 0:
                    val = indices[idc][1][1]
                else:
                    val = next(counter)
                state_idcs.append(val)
                indices[idc][2].append(val)

        # Assigning second operator indices
        for i in range(2):
            for idc in operator_order:
                if i == 0:
                    val = next(counter)
                else:
                    val = indices[idc][2][1]
                op_2_idcs.append(val)
                indices[idc][3].append(val)

        # Assigning resulting indices
        for i in range(2):
            for idc in state_order:
                if idc in operator_order:
                    if i == 0:
                        val = indices[idc][1][0]
                    elif i == 1:
                        val = indices[idc][3][0]
                else:
                    val = indices[idc][2][i]
                result_idcs.append(val)
                        

        #print(f"op_1_idcs: {op_1_idcs}")
        #print(f"state_idcs: {state_idcs}")
        #print(f"op_2_idcs: {op_2_idcs}")
        #print(f"result_idcs:{result_idcs}")

        new_state = np.zeros_like(self.state)
        # Determine the shape of the kraus operators
        kraus_shape = [prop.truncation for prop in operation_spaces]*2
        for K in operators:
            K = K.reshape(kraus_shape)
            new_state += np.einsum(K, op_1_idcs,
                      self.state, state_idcs,
                      K.conj(), op_2_idcs,
                      result_idcs)

        dims = [p.truncation for p in self.state_props]
        self.state = new_state.reshape([np.prod(dims)]*2)

    @Enforcer
    def get_reduced_state(self, spaces:list[StateProp]) -> np.ndarray:
        """
        Returns the reduced state of the system by tracing out the specified subspaces.

        This method computes the reduced density matrix of the system's state over the specified
        subspaces (`spaces`). It effectively traces out the other subsystems not included in 
        `spaces`, resulting in a state that only includes the specified subspaces.

        Parameters
        ----------
        spaces : list[StateProp]
            A list of `StateProp` objects representing the subspaces to retain in the reduced state.
            The state of the system will be traced over all other subsystems not included in this list.

        Returns
        -------
        np.ndarray
            A numpy array representing the reduced density matrix corresponding to the specified 
            subspaces.

        Notes
        -----
        - The method reshapes the current state to a multi-dimensional array corresponding to
        the direct product space of the system's state properties.
        - It uses the Einstein summation convention to perform the partial trace operation, 
        effectively tracing out the subsystems not specified in `spaces`.
        - The original state is not modified by this method.

        Example
        -------
        If `self.state_props` contains subsystems A, B, and C, and `spaces` specifies subsystem A and C,
        then the method will return the reduced density matrix of subsystems A and C, tracing out subsystem B.
        """
        dims = [p.truncation for p in self.state_props]
        out_dims = [p.truncation for p in spaces]
        reshaped_dims = [dim for dim in dims] + [dim for dim in dims]
        self.state = self.state.reshape(reshaped_dims)

        counter = itertools.count(start=0)
        state_order = [prop.uuid for prop in self.state_props]
        
        indices = {}
        for uid in state_order:
            indices[uid] = {
                1: None,
                2: None,
            }

        state_idcs = []
        to_idcs = []
        uid = [x.uuid for x in spaces]

        for i in range(2):
            for idc in state_order:
                if i == 0:
                    val = next(counter)
                    if idc in uid:
                        to_idcs.append(val)
                    state_idcs.append(val)
                    indices[idc][1]=val
                else:
                    if idc in uid:
                        val = next(counter)
                        to_idcs.append(val)
                    else:
                        val = indices[idc][1]
                    state_idcs.append(val)
                    indices[idc][2]=val
        reduced_state = np.einsum(
            self.state, state_idcs,
            to_idcs
        )

        self.state = self.state.reshape([np.prod(dims)]*2)
        return reduced_state.reshape([np.prod(out_dims)]*2)

