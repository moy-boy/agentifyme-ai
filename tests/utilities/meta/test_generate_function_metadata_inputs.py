from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel

from agentifyme.utilities.meta import FunctionMetadata, function_metadata


class SimpleModel(BaseModel):
    value: int


class ComplexModel(BaseModel):
    name: str
    age: Optional[int]
    tags: List[str]


def test_simple_function_without_type_hints():
    def simple_func(x):
        """A simple function that takes a SimpleModel and returns a string."""
        return str(x.value)

    metadata = function_metadata(simple_func)
    assert isinstance(metadata, FunctionMetadata)
    assert metadata.name == "simple_func"
    assert metadata.description == "A simple function that takes a SimpleModel and returns a string."

    print(metadata.input_params)
    # assert len(metadata.input_params) == 1
    # assert metadata.input_params[0].name == "x"
    # assert metadata.input_params[0].data_type == "object"
    # assert len(metadata.output_params) == 1
    # assert metadata.output_params[0].data_type == "string"


def test_simple_function():
    def simple_func(x: SimpleModel) -> str:
        """A simple function that takes a SimpleModel and returns a string."""
        return str(x.value)

    metadata = function_metadata(simple_func)
    assert isinstance(metadata, FunctionMetadata)
    assert metadata.name == "simple_func"
    assert metadata.description == "A simple function that takes a SimpleModel and returns a string."
    assert len(metadata.input_params) == 1
    assert metadata.input_params[0].name == "x.value"
    assert metadata.input_params[0].data_type == "number"
    assert len(metadata.output_params) == 1
    assert metadata.output_params[0].data_type == "string"


def test_complex_function():
    def complex_func(model: ComplexModel, flag: bool = False) -> Union[str, int]:
        """A complex function with multiple parameters and return types."""
        return model.name if flag else model.age or 0

    metadata = function_metadata(complex_func)
    assert isinstance(metadata, FunctionMetadata)
    assert metadata.name == "complex_func"
    assert metadata.description == "A complex function with multiple parameters and return types."

    assert len(metadata.input_params) == 4
    assert {p.name for p in metadata.input_params} == {
        "model.name",
        "model.age",
        "model.tags",
        "flag",
    }
    assert metadata.input_params[0].data_type == "string"  # model.name
    assert metadata.input_params[1].data_type == "number"  # model.age
    assert metadata.input_params[1].required == False  # Optional age
    assert metadata.input_params[2].data_type == "array"  # model.tags
    assert metadata.input_params[3].data_type == "boolean"  # flag
    assert metadata.input_params[3].required == False  # flag has a default value

    assert len(metadata.output_params) == 2
    assert {p.data_type for p in metadata.output_params} == {"string", "number"}


def test_list_function():
    def list_func(items: List[SimpleModel]) -> List[int]:
        """A function that takes a list of SimpleModels and returns a list of integers."""
        return [item.value for item in items]

    metadata = function_metadata(list_func)
    assert isinstance(metadata, FunctionMetadata)
    assert metadata.name == "list_func"
    assert metadata.description == "A function that takes a list of SimpleModels and returns a list of integers."

    assert len(metadata.input_params) == 2
    assert metadata.input_params[0].name == "items"
    assert metadata.input_params[0].data_type == "array"
    assert metadata.input_params[1].name == "items[].value"
    assert metadata.input_params[1].data_type == "number"

    assert len(metadata.output_params) == 1
    assert metadata.output_params[0].data_type == "array"


def test_union_function():
    def union_func(data: Union[str, int, SimpleModel]) -> str:
        """A function that takes a union of types and returns a string."""
        if isinstance(data, SimpleModel):
            return str(data.value)
        return str(data)

    metadata = function_metadata(union_func)
    assert isinstance(metadata, FunctionMetadata)
    assert metadata.name == "union_func"
    assert metadata.description == "A function that takes a union of types and returns a string."

    assert len(metadata.input_params) == 3
    assert {p.name for p in metadata.input_params} == {"data", "data", "data.value"}
    assert {p.data_type for p in metadata.input_params} == {"string", "number"}

    assert len(metadata.output_params) == 1
    assert metadata.output_params[0].data_type == "string"

    # Additional checks
    data_params = [p for p in metadata.input_params if p.name == "data"]
    assert len(data_params) == 2
    assert {p.data_type for p in data_params} == {"string", "number"}

    value_param = next(p for p in metadata.input_params if p.name == "data.value")
    assert value_param.data_type == "number"


# Simple function with one argument
def test_pydantic_input_function():
    def simple_func(x: int) -> str:
        """A simple function that takes an int and returns a string."""
        return str(x)

    metadata = function_metadata(simple_func)
    assert isinstance(metadata, FunctionMetadata)
    assert metadata.name == "simple_func"
    assert metadata.description == "A simple function that takes an int and returns a string."
    assert len(metadata.input_params) == 1
    assert metadata.input_params[0].name == "x"
    assert metadata.input_params[0].data_type == "number"
    assert len(metadata.output_params) == 1
    assert metadata.output_params[0].data_type == "string"


# Function with multiple arguments and default values
def test_multiple_args_with_defaults():
    def multi_arg_func(a: int, b: str = "default", c: float = 1.0) -> bool:
        """A function with multiple arguments and default values."""
        return True

    metadata = function_metadata(multi_arg_func)
    assert len(metadata.input_params) == 3
    assert metadata.input_params[0].name == "a"
    assert metadata.input_params[0].required == True
    assert metadata.input_params[1].name == "b"
    assert metadata.input_params[1].required == False
    assert metadata.input_params[1].default_value == "default"
    assert metadata.input_params[2].name == "c"
    assert metadata.input_params[2].required == False
    assert metadata.input_params[2].default_value == 1.0
    assert len(metadata.output_params) == 1
    assert metadata.output_params[0].data_type == "boolean"


# Function returning a list
def test_function_returning_list():
    def list_func() -> List[str]:
        """A function that returns a list of strings."""
        return ["a", "b", "c"]

    metadata = function_metadata(list_func)
    assert len(metadata.output_params) == 1
    assert metadata.output_params[0].data_type == "array"


# Function with Pydantic BaseModel as input and output
def test_pydantic_input_output():
    class InputModel(BaseModel):
        name: str
        age: int

    class OutputModel(BaseModel):
        greeting: str
        is_adult: bool

    def pydantic_func(input_data: InputModel) -> OutputModel:
        """A function that takes a Pydantic model as input and returns another as output."""
        return OutputModel(greeting=f"Hello, {input_data.name}", is_adult=input_data.age >= 18)

    metadata = function_metadata(pydantic_func)
    assert len(metadata.input_params) == 3
    assert metadata.input_params[0].name == "input_data"
    assert metadata.input_params[0].data_type == "object"
    assert metadata.input_params[1].name == "input_data.name"
    assert metadata.input_params[1].data_type == "string"
    assert metadata.input_params[2].name == "input_data.age"
    assert metadata.input_params[2].data_type == "number"

    assert len(metadata.output_params) == 2
    assert metadata.output_params[0].name == "greeting"
    assert metadata.output_params[0].data_type == "string"
    assert metadata.output_params[1].name == "is_adult"
    assert metadata.output_params[1].data_type == "boolean"


# Function with complex type hints
def test_complex_type_hints():
    def complex_func(a: List[int], b: Optional[Dict[str, Any]] = None) -> Tuple[str, int]:
        """A function with complex type hints."""
        return ("result", 42)

    metadata = function_metadata(complex_func)
    assert len(metadata.input_params) == 2
    assert metadata.input_params[0].name == "a"
    assert metadata.input_params[0].data_type == "array"
    assert metadata.input_params[1].name == "b"
    assert metadata.input_params[1].required == False


# Function with no docstring
def test_no_docstring():
    def no_doc_func(x: int, y: str):
        pass

    metadata = function_metadata(no_doc_func)
    assert metadata.description == ""
    assert len(metadata.input_params) == 2
    assert metadata.input_params[0].description == ""
    assert metadata.input_params[1].description == ""
