This repository is a fork of qsi: https://github.com/tqsd/special_issue_quantum

For the paper "Photonic Unitary Circuits for Quantum Information Processing" part of the Special Issue on Quantum.

# QSI

This repository includes basic codebase for quantum device simulation. The premise of this simulator is that all simulatable devices implement their actions on a particular quantum state in the **quantum channel formalism**, more specifically using Kraus representation. A module represents actions of one device. Since module can be implemented in any language, there needs to be some protocol for communication between the **coordinator** and the modules. This repository implements the protocol for easy integration in Python. Messages are clearly defined, so implementation in other languages should also be relatively easy.


## Installation

We recommend using the repository in a python virtual environment. After the environment has been configured and activated, the **QSI** repository can be installed by:

```
pip install git+https://github.com/mirilab-photonics/software-for-quantum-networks.git@master
```

## Usage

The operation of a module is dictated by the messages received by the coordinator. This protocol defines a set of messages (found in [qsi/messages.py](qsi/messages.py)). All modules must implement responses to all of the messages. The responses must also adhere to the message structure.

When using the `qsi` to define the responses for the module one can simply use

```python
from qsi.qsi import QSI

# Initiate the QSI object instance
qsi = QSI()

# Decorate a function which produces responses to specific messages
@qsi.on_message("state_init"):
def state_init(msg):
	return {
		"msg_type": "state_init_response",
		"states": [],
		"state_ids": []
	}
```

After the object instance `x` of type `QSI` is created any function which returns an appropriate message can be decorated with the decorator `x.on_message('<msg_type>')`. Before the message is sent it's structure and contents are checked by the [qsi/socket_handler.py](qsi/socket_handler.py). 

The list of all messages includes:
 - `param_query`: coordinator querries for all parameters that are required by the module, this is the first message sent by the coordinator. Module should respond with message of type `param_query_response`.
 - `param_set`: coordinator sends the values for the parameters. Module should store those parameters, for later inclusion in the kraus channel computation. It should also respond with message of type `param_set_response`.
 - `state_init`: coordinator requests internal state initialization. If the module has an internal state, it should generate a state and unique id (uuid). It should store the id for later use and send the state back to the coordinator, with message type `state_init_response`. If the module doesn't hold any internal state, then it should respons with empty message.
 - `channel_query`: coordinator requests channel, also providing the states and the ids of the states on which the module should operate. The states are sent as a product state matrix. Based on the stored parameters (and uuids, in case of internal state) the module should compute the channel query and the error bound. Computed Kraus operators, together with other required parameters are then sent back to the coordinator with message type `channel_query_response`.
 - `terminate`: lastly the coordinator requests termination. After receiving this message the module must respond with `terminate_response` and then close the socket server. In the **QSI** implementation this can be easily done with `terminate()` method. (see examples [examples](examples))
