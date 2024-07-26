import numpy as np
import json

def numpy_to_json(matrix):
    """
    Converts a NumPy matrix with complex numbers into a JSON-serializable format.

    Parameters:
    matrix (numpy.ndarray): A matrix with complex numbers.

    Returns:
    list: A JSON-serializable list format of the matrix.
    """
    json_serializable_matrix = matrix.tolist()
    for i in range(len(json_serializable_matrix)):
        for j in range(len(json_serializable_matrix[i])):
            json_serializable_matrix[i][j] = [json_serializable_matrix[i][j].real, json_serializable_matrix[i][j].imag]
    return json_serializable_matrix


def json_to_numpy(json_matrix):
    """
    Converts a JSON-serializable list format back into a NumPy matrix with complex numbers.

    Parameters:
    json_matrix (list): A JSON-serializable list format of the matrix.

    Returns:
    numpy.ndarray: A NumPy matrix with complex numbers.
    """
    complex_matrix = np.empty((len(json_matrix), len(json_matrix[0])), dtype=np.complex128)
    for i in range(len(json_matrix)):
        for j in range(len(json_matrix[i])):
            real_part, imag_part = json_matrix[i][j]
            complex_matrix[i, j] = complex(real_part, imag_part)
    return complex_matrix

def pretty_print_dict(d):
    print(json.dumps(d, indent=4))
