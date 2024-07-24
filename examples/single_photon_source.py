from qsi.qsi import QSI
import time

qsi = QSI()

@qsi.on_message("state_init")
def state_init(msg):
    print(msg)
    return {
        "msg_type": "state_init_response",
        "states": [],
        "state_ids": [],
        "variables": []
    }
    
qsi.run()
time.sleep(1)
