from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, Field

from agentifyme.utilities.meta import FunctionMetadata, Param, function_metadata


def simple_function(x: int, y: float = 1.0) -> str:
    """A simple function."""
    return str(x + y)


class MyModel(BaseModel):
    value: int


class SimpleModel(BaseModel):
    value: int


class ComplexModel(BaseModel):
    name: str
    age: Optional[int]
    tags: List[str]


def function_with_model(x: int) -> MyModel:
    """Function returning a model."""
    return MyModel(value=x)


def function_with_model_or_none(x: int) -> Union[MyModel, None]:
    """Function returning a model or None."""
    return MyModel(value=x)


def function_with_list_return(x: int) -> List[str]:
    """Function returning a list of strings."""
    return [str(x)]


def function_with_empty_return(x: int) -> None:
    """Function returning None."""
    pass


def test_simple_function_metadata():
    metadata = function_metadata(simple_function)
    assert metadata.name == "simple_function"
    assert metadata.description == "A simple function."
    assert len(metadata.input_params) == 2
    assert metadata.input_params[0] == Param(name="x", description="", data_type="number", default_value=None, required=True)
    assert metadata.input_params[1] == Param(name="y", description="", data_type="number", default_value=1.0, required=False)
    assert len(metadata.output_params) == 1
    assert metadata.output_params[0] == Param(
        name="output",
        description="",
        data_type="string",
        default_value="",
        required=True,
    )
    assert metadata.doc_string == "A simple function."


# Test for function with model return type
def test_function_with_model_metadata():
    metadata = function_metadata(function_with_model)
    assert metadata.name == "function_with_model"
    assert metadata.description == "Function returning a model."
    assert len(metadata.input_params) == 1
    assert metadata.input_params[0] == Param(name="x", description="", data_type="number", default_value=None, required=True)
    assert len(metadata.output_params) == 1
    assert metadata.output_params[0] == Param(
        name="value",
        description="",
        data_type="number",
        default_value=None,
        required=True,
    )
    assert metadata.doc_string == "Function returning a model."


def test_function_with_model_or_none_metadata():
    metadata = function_metadata(function_with_model_or_none)
    assert metadata.name == "function_with_model_or_none"
    assert metadata.description == "Function returning a model or None."
    assert len(metadata.input_params) == 1
    assert metadata.input_params[0] == Param(name="x", description="", data_type="number", default_value=None, required=True)
    assert len(metadata.output_params) == 1
    assert metadata.output_params[0] == Param(
        name="value",
        description="",
        data_type="number",
        default_value=None,
        required=True,
    )
    assert metadata.doc_string == "Function returning a model or None."


# Test for function returning list
def test_function_with_list_return_metadata():
    metadata = function_metadata(function_with_list_return)
    assert metadata.name == "function_with_list_return"
    assert metadata.description == "Function returning a list of strings."
    assert len(metadata.input_params) == 1
    assert metadata.input_params[0] == Param(name="x", description="", data_type="number", default_value=None, required=True)
    assert len(metadata.output_params) == 1
    assert metadata.output_params[0] == Param(
        name="output",
        description="",
        data_type="array",
        default_value=[],
        required=True,
    )
    assert metadata.doc_string == "Function returning a list of strings."


# Test for function with None return type
def test_function_with_empty_return_metadata():
    metadata = function_metadata(function_with_empty_return)
    assert metadata.name == "function_with_empty_return"
    assert metadata.description == "Function returning None."
    assert len(metadata.input_params) == 1
    assert metadata.input_params[0] == Param(name="x", description="", data_type="number", default_value=None, required=True)
    assert len(metadata.output_params) == 0
    assert metadata.doc_string == "Function returning None."


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


# Test edge cases
def test_edge_cases():
    # Function with *args and **kwargs
    def variadic_func(*args, **kwargs):
        """A function with variadic arguments."""
        pass

    metadata = function_metadata(variadic_func)
    assert len(metadata.input_params) == 0  # *args and **kwargs are not included

    # Function with no parameters
    def no_params_func():
        """A function with no parameters."""
        pass

    metadata = function_metadata(no_params_func)
    assert len(metadata.input_params) == 0

    # Function with no return annotation
    def no_return_func(x: int):
        """A function with no return annotation."""
        pass

    metadata = function_metadata(no_return_func)
    assert len(metadata.output_params) == 0


# Test function with Union types
def test_union_types():
    def union_func(x: Union[int, str]) -> Union[float, bool]:
        """A function with Union types."""
        return 1.0 if isinstance(x, int) else True

    metadata = function_metadata(union_func)
    assert len(metadata.input_params) == 1
    assert metadata.input_params[0].name == "x"
    assert metadata.input_params[0].data_type == "string"  # Default to string for complex types
    assert len(metadata.output_params) == 1
    assert metadata.output_params[0].data_type == "number"  # Default to number for Union[float, bool]


# Test function with nested Pydantic models
def test_nested_pydantic_models():
    class InnerModel(BaseModel):
        value: int

    class OuterModel(BaseModel):
        name: str
        inner: InnerModel

    def nested_model_func(data: OuterModel) -> List[InnerModel]:
        """A function with nested Pydantic models."""
        return [data.inner]

    metadata = function_metadata(nested_model_func)
    assert len(metadata.input_params) == 1
    assert metadata.input_params[0].name == "data"
    assert len(metadata.output_params) == 1
    assert metadata.output_params[0].data_type == "array"


# Test function with complex return type annotation
def test_complex_return_type():
    def complex_return_func() -> Dict[str, List[Tuple[int, str]]]:
        """A function with a complex return type."""
        return {"result": [(1, "a"), (2, "b")]}

    metadata = function_metadata(complex_return_func)
    assert len(metadata.output_params) == 1
    assert metadata.output_params[0].data_type == "string"  # Default to string for complex types


# Test function with type annotations from 'typing' module
def test_typing_annotations():
    from typing import Any, Sequence

    def typing_func(x: Sequence[Any]) -> Optional[Dict[str, Any]]:
        """A function with annotations from the typing module."""
        return None

    metadata = function_metadata(typing_func)
    assert len(metadata.input_params) == 1
    assert metadata.input_params[0].name == "x"
    assert metadata.input_params[0].data_type == "array"  # Sequence is treated as array
    assert len(metadata.output_params) == 1
    assert metadata.output_params[0].data_type == "string"  # Default to string for complex types


# Test function with Pydantic model using Field
def test_pydantic_field():
    class ModelWithField(BaseModel):
        name: str = Field(..., description="The name field")
        age: int = Field(default=0, description="The age field")

    def field_func(data: ModelWithField) -> str:
        """A function with a Pydantic model using Field."""
        return f"{data.name} is {data.age} years old"

    metadata = function_metadata(field_func)
    assert len(metadata.input_params) == 1
    assert metadata.input_params[0].name == "data"
    assert len(metadata.output_params) == 1
    assert metadata.output_params[0].data_type == "string"


# Test function with callable parameter
def test_callable_parameter():
    def higher_order_func(func: Callable[[int], str]) -> Callable[[str], int]:
        """A higher-order function with callable parameters."""

        def wrapper(s: str) -> int:
            return len(func(len(s)))

        return wrapper

    metadata = function_metadata(higher_order_func)
    assert len(metadata.input_params) == 1
    assert metadata.input_params[0].name == "func"
    assert metadata.input_params[0].data_type == "string"  # Default to string for complex types
    assert len(metadata.output_params) == 1
    assert metadata.output_params[0].data_type == "string"  # Default to string for complex types


# Test function with generic types
def test_generic_types():
    from typing import Generic, TypeVar

    T = TypeVar("T")

    class GenericClass(Generic[T]):
        def __init__(self, value: T):
            self.value = value

    def generic_func(data: GenericClass[int]) -> GenericClass[str]:
        """A function with generic types."""
        return GenericClass(str(data.value))

    metadata = function_metadata(generic_func)
    assert len(metadata.input_params) == 1
    assert metadata.input_params[0].name == "data"
    assert metadata.input_params[0].data_type == "string"  # Default to string for complex types
    assert len(metadata.output_params) == 1
    assert metadata.output_params[0].data_type == "string"  # Default to string for complex types


# Test function with complex docstring
def test_complex_docstring():
    def complex_doc_func(a: int, b: str) -> bool:
        """
        A function with a complex docstring.

        This function does something complex.

        Args:
            a (int): The first parameter.
            b (str): The second parameter.

        Returns:
            bool: The result of the complex operation.

        Raises:
            ValueError: If a is negative.

        Examples:
            >>> complex_doc_func(1, "test")
            True
        """
        if a < 0:
            raise ValueError("'a' must be non-negative")
        return len(b) == a

    metadata = function_metadata(complex_doc_func)
    assert metadata.description == "A function with a complex docstring."
    assert len(metadata.input_params) == 2
    assert metadata.input_params[0].name == "a"
    assert metadata.input_params[0].description == "The first parameter."
    assert metadata.input_params[1].name == "b"
    assert metadata.input_params[1].description == "The second parameter."
    assert len(metadata.output_params) == 1
    assert metadata.output_params[0].description == "The result of the complex operation."
