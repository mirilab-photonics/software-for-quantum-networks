import subprocess
import threading

from qsi.helpers import numpy_to_json, json_to_numpy
from qsi.state import State, StateProp

class ModuleReference:
    def __init__(self, module: str, port: int, coordinator_port: int, runtime: str, coordinator: "Coordinator"):
        self.coordinator = coordinator
        self.module = module
        self.port = port
        self.runtime = runtime
        self.states = []
        self.params = []
        if runtime == "python":
            command = ["python", module, str(port), str(coordinator_port)]
        print(command)
        self.process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.events = {
            "params_known": threading.Event()
        }
        
        # Start threads to capture stdout and stderr
        threading.Thread(target=self._capture_output, args=(self.process.stdout, "stdout")).start()
        threading.Thread(target=self._capture_output, args=(self.process.stderr, "stderr")).start()

    def notify_params(self, params):
        self.events["params_known"].set()
        self.params = {
            x[0]:{"type":x[1], "value":None} for x in params
        }

    def _capture_output(self, stream, stream_name):
        for line in iter(stream.readline, ''):
            print(f"[{stream_name}] {line.strip()}")
        stream.close()

    def apply_kraus_operators(state=None):
        if state is None and not len(self.states) == 1:
            raise FalseInternalStateNumber(f"Excpected to contain one internal state, but have {len(self.states)}")

    def _operate_with_kraus_operators(self):
        pass

    def state_init_response(self):
        print("State init response")

    def set_param(self, param, value):
        self.events["params_known"].wait()
        print(param, value)
        print(self.params)
        if self.params[param]["type"]=="complex":
            num = complex(value)
            self.params[param]["value"] = [num.real, num.imag]
        else:
            self.params[param]["value"] = value

    def send_params(self):
        message = {
            "msg_type":"param_set",
            "params":self.params
        }
        self.coordinator.send_to(self.port, message)

    def state_init(self):
        message = {
            "msg_type" : "state_init"
        }
        response = self.coordinator.send_and_return_response(self.port, message)
        print("\n\n")
        print(response)
        states = []
        for s in response["states"]:
            states.append(State.from_message(s))
        return states
        
    def channel_query(self, state: "State", port_assign):
        """
        Queries the module for the Kraus channel
        """
        message = state.to_message(port_assign)
        message["msg_type"]="channel_query"
        response = self.coordinator.send_and_return_response(self.port, message)
        if "kraus_operators" in response:
            operators = [json_to_numpy(x) for x in response["kraus_operators"]]

        return operators, float(response["error"])


    def terminate(self):
        proc = self.process
        try:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
        except Exception as e:
            print(f"Exception while terinating subprocess: {e}")
                    

