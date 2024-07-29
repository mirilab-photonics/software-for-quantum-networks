"""
Simple Quantum State Handler
"""
from dataclasses import dataclass, field, asdict
import numpy as np
from typing import Literal, Optional
import uuid

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

    def get_props(self, uuid:str) -> dict:
        return self.state_props[self.get_index(uuid)]


    def apply_kraus_operators(self, operators: list):
        new_state = None
        for op in operators:
            if new_state is None:
                new_state = op @ self.state @ op.conjugate().T
            else:
                new_state += op @ self.state @ op.conjugate().T
        self.state = new_state

    def get_props(self, uuid) -> StateProp:
        return [x for x in self.state_props if x.uuid == uuid][0]
