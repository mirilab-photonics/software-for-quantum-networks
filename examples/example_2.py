# Imports
import numpy as np
import uuid
from qsi.coordinator import Coordinator
from qsi.state import State, StateProp

# Create coordinator and start the modules:
coordinator = Coordinator(port=10000)
# Coherent source
cs = coordinator.register_componnet(module="coherent_source.py", runtime="python")

# Run the coordinator process
coordinator.run()
cs.set_param("alpha", 1+0j)
cs.send_params()
# Generate the space for coherent state
coherent_state_prop = StateProp(
    state_type="light",
    truncation=10,
    wavelength=1550,
    polarization="R"
)
coherent_state = State(coherent_state_prop)
# Get the Kraus operator for the generation of the coherent state
response = cs.channel_query(
    coherent_state, {"input": coherent_state_prop.uuid}
)

print(response)
#state_one.apply_kraus_operators(sps_kraus, [coherent_state_prop])
