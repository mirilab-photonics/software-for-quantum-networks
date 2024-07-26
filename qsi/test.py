import jsonschema
from jsonschema import validate
from jsonschema.exceptions import ValidationError

# Define the JSON schema
param_query_response_schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "msg_type": {"type": "string", "enum": ["param_set_response"]},
        "sent_from": {"type": "integer"},
        "params": {
            "type": "array",
            "items": {
                "type": "array",
                "minItems": 2,
                "maxItems": 2,
                "items": [
                    {"type": "string"},
                    {"type": "string", "enum": ["integer", "number", "string"]}
                ]
            },
            "uniqueItems": True
        }
    },
    "required": ["msg_type", "sent_from"],
    "additionalProperties": False
}

# Function to validate JSON data against the schema
def validate_json(data):
    try:
        validate(instance=data, schema=param_query_response_schema)
        print("JSON data is valid")
    except ValidationError as err:
        print("JSON data is invalid:", err)

# Example JSON data that should match the schema
data_to_validate = {
    "msg_type": "param_set_response",
    "sent_from": 1000
}
validate_json(data_to_validate)

# Valid Data with Params
data_with_params = {
    "msg_type": "param_set_response",
    "sent_from": 1000,
    "params": [
        ["param1", "integer"],
        ["param2", "number"],
        ["param3", "string"]
    ]
}
validate_json(data_with_params)

# Valid Data with Empty Params
data_empty_params = {
    "msg_type": "param_set_response",
    "sent_from": 1000,
    "params": []
}
validate_json(data_empty_params)

# Invalid Data (Wrong Type in Params)
invalid_data_wrong_type = {
    "msg_type": "param_set_response",
    "sent_from": 1000,
    "params": [
        ["param1", "integer"],
        ["param2", "invalid_type"]
    ]
}
validate_json(invalid_data_wrong_type)

# Invalid Data (Missing Required Field)
invalid_data_missing_field = {
    "msg_type": "param_set_response"
}
validate_json(invalid_data_missing_field)
