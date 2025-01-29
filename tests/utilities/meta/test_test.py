import inspect
from typing import Any, Dict, Union, get_type_hints

from pydantic import BaseModel


class InputModel(BaseModel):
    field1: int
    field2: str


class OutputModel(BaseModel):
    result: str


def pydantic_function(
    input_data: InputModel,
) -> Union[OutputModel, None, Dict[str, Any]]:
    """
    A function using Pydantic models with detailed docstring.

    Args:
        input_data (InputModel): The input data model.
            field1 (int): An integer field in the input model.
            field2 (str): A string field in the input model.

    Returns:
        OutputModel: The output data model.
            result (str): The resulting string in the output model.
    """
    return OutputModel(result=f"{input_data.field1}: {input_data.field2}")


def extract_function_params(func):
    # Get the function's docstring
    docstring = inspect.getdoc(func)

    # Get type hints
    type_hints = get_type_hints(func)

    # Extract input parameters
    input_params = {}
    for name, annotation in type_hints.items():
        if name != "return":
            input_params[name] = str(annotation)

    # Extract output parameter
    output_param = str(type_hints.get("return", "None"))

    # Parse docstring for detailed parameter information
    detailed_params = {}
    current_section = None
    if docstring:
        for line in docstring.split("\n"):
            line = line.strip()
            if line.startswith("Args:"):
                current_section = "args"
            elif line.startswith("Returns:"):
                current_section = "returns"
            elif current_section == "args" and ":" in line:
                param, description = line.split(":", 1)
                detailed_params[param.strip()] = description.strip()
            elif current_section == "returns" and ":" in line:
                param, description = line.split(":", 1)
                detailed_params["return"] = description.strip()

        return {
            "input_params": input_params,
            "output_param": output_param,
            "detailed_params": detailed_params,
        }


def test_simple_function():
    # Example usage
    result = extract_function_params(pydantic_function)
    assert result is not None
    assert isinstance(result, dict)
    assert "input_params" in result
    assert "output_param" in result
    assert "detailed_params" in result
