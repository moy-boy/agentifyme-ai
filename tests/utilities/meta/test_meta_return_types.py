from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, Field

from agentifyme.utilities.meta import Param, function_metadata


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
    from typing import Sequence

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
