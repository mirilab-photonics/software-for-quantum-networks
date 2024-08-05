"""
Example 01
-------------------
Example with:
 - Single Photon Source
 - Memory
"""

import numpy as np
import uuid
from qsi.coordinator import Coordinator
from qsi.state import State, StateProp


# Initiate the Coordinator
coordinator = Coordinator()

# Start the module processes, before running the coordinator process
sps = coordinator.register_componnet(
    module="single_photon_source.py", runtime="python")
mem = coordinator.register_componnet(module="memory.py", runtime="python")

# Run the coordinator, when the coordinator starts, it automatically queries
# all modules for the possible parameters to set. ('param_query')
coordinator.run()

# Set the parameters of the devices one by one
# This is an example, this value is not actually used in the simulation
sps.set_param("test", 2+1j)

# Set all configured parameters to the device ('param_set')
sps.send_params()

# Initialize internal states if device has any ('state_init')
sps.state_init()
state_mem = mem.state_init()[0]

state_one = State(StateProp(
    state_type="light",
    truncation=3,
    wavelength=1550,
    polarization="R"
))

sps_kraus, sps_kraus_spaces, error, retry = sps.channel_query(
    state_one, {"input": state_one.state_props[0].uuid}
)
state_one.apply_kraus_operators(
    sps_kraus, state_one.get_all_props(sps_kraus_spaces))

state_one.join(state_mem)

mem_kraus, mem_kraus_spaces, error, retry = mem.channel_query(
    state_one, {"input": state_one.state_props[0].uuid}
)

state_one.apply_kraus_operators(
    mem_kraus, state_one.get_all_props(mem_kraus_spaces))


coordinator.terminate()
