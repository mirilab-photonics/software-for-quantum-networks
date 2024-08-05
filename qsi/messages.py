"""
This module is used for message verification
"""

import jsonschema


param_query = {
    "msg_type" : {"type": "string", "enum":["param_query"]},
    "sent_from" : "int"
}

param_query_response = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "msg_type": {"type": "string", "enum": ["param_query_response"]},
        "sent_from": {"type": "integer"},
        "params": {
            "type": "object",
            "patternProperties": {
                "^[a-zA-Z_][a-zA-Z0-9_]*$": {
                    "type": "string",
                    "enum": ["integer", "number", "string", "complex"]
                }
            }
        }
    },
    "required": ["msg_type", "sent_from"],
    "additionalProperties": False
}

param_set = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "msg_type": {"type": "string", "enum": ["param_set"]},
        "sent_from": {"type": "integer"},
        "params": {
            "type": "object",
            "patternProperties": {
                "^.*$": {
                    "type": "object",
                    "properties": {
                        "value": {}
                    },
                    "required": ["value"],
                    "additionalProperties": True
                }
            },
            "additionalProperties": True
        }
    },
    "required": ["msg_type", "sent_from", "params"],
    "additionalProperties": False
}

param_set_response = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "msg_type": {"type": "string", "enum": ["param_set_response"]},
        "sent_from": {"type": "integer"}
    }
}

state_init = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "msg_type": {"type": "string", "enum": ["state_init"]},
        "sent_from": {"type": "integer"}
    }
}

state_init_response = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "msg_type": {"type": "string", "enum": ["state_init_response"]},
        "sent_from": {"type": "integer"}
    }
}

channel_query = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "msg_type": {"type": "string", "enum": ["channel_query"]},
        "sent_from": {"type": "integer"}
    }
}

channel_query_response = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "msg_type": {"type": "string", "enum": ["channel_query_response"]},
        "sent_from": {"type": "integer"},
        "error": {"type": "number"},
        "message": {"type": "string"},
        "operation_time": {"type": "number"},
        "retrigger": {"type": "boolean"},
        "retrigger_time": {"type": "number"},
        "kraus_operators": {
            "type": "array",
            "items": {  # list of operators
                "type": "array",
                "items": {  # row of an operator
                    "type": "array",
                    "items": {  # column of an operator
                        "type": "array",
                        "items": {  # element of an operator
                            "type": "number"
                        },
                        "minItems": 2,
                        "maxItems": 2
                    }
                }
            }
        },
        "kraus_state_indices": {
            "type": "array",
            "items": {
                "type": "string",
                "minItems": 1
            }
        }
    },
    "anyOf": [
        {"required": ["kraus_operators", "error", "kraus_state_indices"]},
        {"required": ["message"]},
        {"required": ["retrigger", "retrigger_time"]}
    ],
    "required": ["msg_type", "sent_from"],
}

terminate = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "msg_type": {"type": "string", "enum": ["terminate"]},
    }
}

terminate_response = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "msg_type": {"type": "string", "enum": ["terminate_response"]},
    }
}

SCHEMAS = {
    "param_query": param_query,
    "param_query_response": param_query_response,
    "param_set": param_set,
    "param_set_response": param_set_response,
    "state_init": state_init,
    "state_init_response": state_init_response,
    "channel_query":channel_query,
    "channel_query_response":channel_query_response,
    "terminate":terminate,
    "terminate_response":terminate_response
}
