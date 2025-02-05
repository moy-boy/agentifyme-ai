from datetime import datetime
from decimal import Decimal
from typing import Any, Optional, Union

import pytest
from pydantic import BaseModel

# Import the function to test
from agentifyme.worker.helpers import build_args_from_signature


# Test helper classes and functions
class SimpleModel(BaseModel):
    value: int
    name: str


def func_with_basic_types(a: int, b: float, c: str):
    pass


def func_with_optional(a: Optional[int], b: Optional[str] = None):
    pass


def func_with_union(a: Union[int, float], b: Union[str, int]):
    pass


def func_with_decimal(amount: Decimal, description: str):
    pass


def func_with_datetime(timestamp: datetime, note: str):
    pass


def func_with_pydantic(model: SimpleModel, count: int):
    pass


def func_with_dict(filters: dict, settings: dict[str, int], config: dict[str, Any] = None):
    pass


def func_with_nested_dict(filters: dict[str, dict[str, str]], counts: dict[str, int], metrics: dict[str, Union[int, float]]):
    pass


# Basic type conversion tests
def test_basic_type_conversion():
    input_dict = {"a": "42", "b": "3.14", "c": "hello"}
    result = build_args_from_signature(func_with_basic_types, input_dict)
    assert result == {"a": 42, "b": 3.14, "c": "hello"}
    assert isinstance(result["a"], int)
    assert isinstance(result["b"], float)
    assert isinstance(result["c"], str)


def test_numeric_conversion():
    # Test integer conversion
    input_dict = {"a": 42.0, "b": 3.14, "c": "test"}
    result = build_args_from_signature(func_with_basic_types, input_dict)
    assert result["a"] == 42
    assert isinstance(result["a"], int)

    # Test float that can't be converted to int
    with pytest.raises(ValueError, match="cannot be converted to integer without loss"):
        build_args_from_signature(func_with_basic_types, {"a": 42.5, "b": 1.0, "c": "test"})


# Optional type tests
def test_optional_types():
    # First, let's properly define what Optional looks like in the type hints
    from typing import get_args, get_origin

    def is_optional(field_type):
        return get_origin(field_type) is Union and type(None) in get_args(field_type)

    # Test with None values for optional parameters
    input_dict = {"a": None, "b": None}
    result = build_args_from_signature(func_with_optional, input_dict)
    assert result == {"a": None, "b": None}

    # Test with actual values
    input_dict = {"a": "42", "b": "hello"}
    result = build_args_from_signature(func_with_optional, input_dict)
    assert result == {"a": 42, "b": "hello"}

    # Test mixing None and actual values
    input_dict = {"a": "42", "b": None}
    result = build_args_from_signature(func_with_optional, input_dict)
    assert result == {"a": 42, "b": None}


# Union type tests
def test_union_types():
    # Test first union type (float)
    input_dict = {"a": "42.5", "b": "123"}
    result = build_args_from_signature(func_with_union, input_dict)
    assert result == {"a": 42.5, "b": "123"}
    assert isinstance(result["a"], float)

    # Test second union type (int)
    input_dict = {"a": "42", "b": 123}
    result = build_args_from_signature(func_with_union, input_dict)
    assert result["a"] == 42
    assert isinstance(result["a"], int)
    assert result["b"] == "123"  # b should be string
    assert isinstance(result["b"], str)

    # Test string input for integer union
    input_dict = {"a": "42", "b": "456"}
    result = build_args_from_signature(func_with_union, input_dict)
    assert result["b"] == "456"  # b should stay as string
    assert isinstance(result["b"], str)


# Decimal type tests
def test_decimal_conversion():
    input_dict = {"amount": "123.45", "description": "test payment"}
    result = build_args_from_signature(func_with_decimal, input_dict)
    assert isinstance(result["amount"], Decimal)
    assert result["amount"] == Decimal("123.45")

    # Test invalid decimal
    with pytest.raises(ValueError):
        build_args_from_signature(func_with_decimal, {"amount": "invalid", "description": "test"})


# DateTime tests
def test_datetime_conversion():
    # Test ISO format
    input_dict = {"timestamp": "2024-02-04T12:00:00Z", "note": "test"}
    result = build_args_from_signature(func_with_datetime, input_dict)
    assert isinstance(result["timestamp"], datetime)
    assert result["timestamp"].isoformat() == "2024-02-04T12:00:00+00:00"

    # Test passing datetime object directly
    dt = datetime.now()
    input_dict = {"timestamp": dt, "note": "test"}
    result = build_args_from_signature(func_with_datetime, input_dict)
    assert result["timestamp"] == dt


# Pydantic model tests
def test_pydantic_model():
    input_dict = {"model": {"value": 42, "name": "test"}, "count": 1}
    result = build_args_from_signature(func_with_pydantic, input_dict)
    assert isinstance(result["model"], SimpleModel)
    assert result["model"].value == 42
    assert result["model"].name == "test"


# Dictionary type tests
def test_basic_dict():
    input_dict = {
        "filters": {"status": "active", "type": "user"},
        "settings": {"timeout": 30, "retries": 3},
    }
    result = build_args_from_signature(func_with_dict, input_dict)
    assert result["filters"] == {"status": "active", "type": "user"}
    assert result["settings"] == {"timeout": 30, "retries": 3}
    assert isinstance(result["filters"], dict)
    assert isinstance(result["settings"], dict)


def test_dict_with_optional():
    # Test with config provided
    input_dict = {"filters": {"status": "active"}, "settings": {"timeout": 30}, "config": {"debug": True}}
    result = build_args_from_signature(func_with_dict, input_dict)
    assert result["config"] == {"debug": True}
    assert isinstance(result["config"], dict)

    # Test without optional config
    input_dict = {"filters": {"status": "active"}, "settings": {"timeout": 30}}
    result = build_args_from_signature(func_with_dict, input_dict)
    assert "config" not in result

    # Test with None config
    input_dict = {"filters": {"status": "active"}, "settings": {"timeout": 30}, "config": None}
    result = build_args_from_signature(func_with_dict, input_dict)
    assert result["config"] is None


def test_nested_dict():
    input_dict = {
        "filters": {"user": {"role": "admin", "status": "active"}, "org": {"type": "business", "tier": "premium"}},
        "counts": {"users": 100, "orgs": 50},
        "metrics": {"score": 42, "ratio": 0.75},
    }
    result = build_args_from_signature(func_with_nested_dict, input_dict)

    # Check outer structure
    assert isinstance(result["filters"], dict)
    assert isinstance(result["counts"], dict)
    assert isinstance(result["metrics"], dict)

    # Check nested types
    assert all(isinstance(v, dict) for v in result["filters"].values())
    assert all(isinstance(v, int) for v in result["counts"].values())
    assert isinstance(result["metrics"]["score"], int)
    assert isinstance(result["metrics"]["ratio"], float)


def test_dict_type_conversion():
    # Test with string numbers that should be converted
    input_dict = {
        "filters": {"status": "active"},
        "settings": {"timeout": "30", "retries": "3"},  # String numbers
    }
    result = build_args_from_signature(func_with_dict, input_dict)
    assert isinstance(result["settings"]["timeout"], int)
    assert isinstance(result["settings"]["retries"], int)
    assert result["settings"] == {"timeout": 30, "retries": 3}


def test_invalid_dict_types():
    # Test with non-dict value for dict parameter
    with pytest.raises(ValueError) as exc_info:
        build_args_from_signature(func_with_dict, {"filters": ["not", "a", "dict"], "settings": {"timeout": 30}})
    assert str(exc_info.value) == "Expected dict but got list"

    # Test with invalid type in typed dict values
    with pytest.raises(ValueError) as exc_info:
        build_args_from_signature(func_with_dict, {"filters": {"status": "active"}, "settings": {"timeout": "invalid", "retries": 3}})
    assert "Cannot convert" in str(exc_info.value)


# Error cases
def test_missing_required_parameter():
    with pytest.raises(ValueError, match="Required parameter"):
        build_args_from_signature(func_with_basic_types, {"a": 1, "c": "test"})


def test_invalid_type_conversion():
    with pytest.raises(ValueError):
        build_args_from_signature(func_with_basic_types, {"a": "not_a_number", "b": 1.0, "c": "test"})


def test_none_for_required_parameter():
    with pytest.raises(ValueError, match="Required parameter"):
        build_args_from_signature(func_with_basic_types, {"a": None, "b": 1.0, "c": "test"})
