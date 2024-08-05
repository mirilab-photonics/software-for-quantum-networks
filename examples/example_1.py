# Imports
import numpy as np
import uuid
from qsi.coordinator import Coordinator
from qsi.state import State, StateProp

# Create coordinator and start the modules:
coordinator = Coordinator(port=25000)
# Coherent source
cs = coordinator.register_component(module="coherent_source.py", runtime="python")
fib = coordinator.register_component(module="fiber.py", runtime="python")

# Run the coordinator process
coordinator.run()

# Configure the module parameters
cs.set_param("alpha", 1+0j)
cs.send_params()

fib.set_param("length", 10)
fib.set_param("n", 1.45)
fib.send_params()

# Generate the space for coherent state
coherent_state_prop = StateProp(
    state_type="light",
    truncation=10,
    wavelength=1550,
    polarization="R"
)
coherent_state = State(coherent_state_prop)

# Get Kraus operators for the generation of the coherent state
response, operators = cs.channel_query(
    coherent_state, {"input": coherent_state_prop.uuid}
)
print(response["error"])

# Apply Kraus operators to the state
coherent_state.apply_kraus_operators(
    operators,
    coherent_state.get_all_props(response["kraus_state_indices"])
)

# Get Kraus operators for the fiber
response, operators = fib.channel_query(
    coherent_state, {"input": coherent_state_prop.uuid}
)

# Apply Kraus operators for the fiber
coherent_state.apply_kraus_operators(
    operators,
    coherent_state.get_all_props(response["kraus_state_indices"])
)
