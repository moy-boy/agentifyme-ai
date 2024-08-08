from typing import Dict, List

import pytest
from docstring_parser import parse

from agentifyme.utilities.func_utils import (
    get_function_metadata,
    get_input_parameters,
    get_output_parameters,
)


def test_get_input_parameters():
    def sample_func(a: int, b: str = "default"):
        return

    parsed_docstring = parse("Sample function")
    input_params = get_input_parameters(sample_func, parsed_docstring)

    assert len(input_params) == 2
    assert input_params["a"].data_type == "number"
    assert input_params["a"].required == True
    assert input_params["b"].data_type == "string"
    assert input_params["b"].default_value == "default"
    assert input_params["b"].required == False


def test_get_output_parameters():
    def sample_func() -> int:
        return 10

    parsed_docstring = parse("Sample function\n\nReturns:\n    int: A number")
    output_params = get_output_parameters(sample_func, parsed_docstring)

    assert len(output_params) == 1
    assert output_params[0].data_type == "number"
    assert output_params[0].description == "A number"


def test_get_function_metadata():
    def add(a: int, b: int = 0) -> int:
        """
        Add two numbers.

        Args:
            a (int): First number
            b (int): Second number, defaults to 0

        Returns:
            int: The sum of a and b
        """
        return a + b

    metadata = get_function_metadata(add)

    assert metadata.name == "add"
    assert metadata.description == "Add two numbers."
    assert len(metadata.input_parameters) == 2
    assert metadata.input_parameters["a"].required == True
    assert metadata.input_parameters["b"].required == False
    assert metadata.input_parameters["b"].default_value == 0
    assert len(metadata.output_parameters) == 1
    assert metadata.output_parameters[0].description == "The sum of a and b"


def identity(x: str) -> str:
    return x


def add_int(x: int) -> int:
    return x + 1


def add_float(x: float) -> float:
    return x + 1.0


def to_string(x: int) -> str:
    return str(x)


def return_bool() -> bool:
    return True


def return_list() -> List[int]:
    return [1, 2, 3]


def return_dict() -> Dict[str, str]:
    return {"key": "value"}


@pytest.mark.parametrize(
    "func, expected_type",
    [
        (identity, "string"),
        (add_int, "number"),
        (add_float, "number"),
        (to_string, "string"),
        (return_bool, "boolean"),
        (return_list, "array"),
        (return_dict, "object"),
    ],
)
def test_json_datatype_from_python_type(func, expected_type):
    metadata = get_function_metadata(func)
    assert metadata.output_parameters[0].data_type == expected_type
