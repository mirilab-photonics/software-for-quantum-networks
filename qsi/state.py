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

    def merge(self, other: "State"):
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
        Traces out the state and returns the subspace with the giben uid.
        Does not modify the state.
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
