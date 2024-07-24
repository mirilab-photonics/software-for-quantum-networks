"""
Coordinator example
-------------------
Coordinator runs the example modules
"""
from qsi.coordinator import Coordinator
coordinator = Coordinator()
sps = coordinator.register_componnet(module="single_photon_source.py", runtime="python")

if __name__ == "__main__":
    coordinator.run()
