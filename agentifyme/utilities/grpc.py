import base64
import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Callable, Dict, Type

# Try importing optional dependencies
try:
    import numpy as np

    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    from pydantic import BaseModel

    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False


def generate_short_uuid():
    uuid_bytes = uuid.uuid4().bytes
    short = base64.urlsafe_b64encode(uuid_bytes).decode("ascii")
    return short.rstrip("=")


def get_message_id():
    return f"msg_{generate_short_uuid()}"


def get_run_id():
    return f"run_{generate_short_uuid()}"


def get_timestamp():
    return int(datetime.now().timestamp() * 1_000_000)


# Type conversion functions
def convert_datetime(data: datetime | date) -> str:
    return data.isoformat()


def convert_decimal(data: Decimal) -> float:
    return float(data)


def convert_uuid(data: uuid.UUID) -> str:
    return str(data)


def convert_enum(data: Enum) -> str:
    return data.value


def convert_sequence(data: list | tuple | set) -> list:
    return [convert_for_protobuf(v) for v in data]


def convert_dict(data: dict) -> dict:
    return {k: convert_for_protobuf(v) for k, v in data.items()}


# Optional numpy converters
def convert_numpy_number(data: Any) -> float:
    return data.item()


def convert_numpy_array(data: Any) -> list:
    return convert_for_protobuf(data.tolist())


# Optional pydantic converter
def convert_pydantic(data: Any) -> dict:
    return convert_for_protobuf(data.model_dump())


# Build type registry
TYPE_CONVERTERS: Dict[Type, Callable] = {
    dict: convert_dict,
    (list, tuple, set): convert_sequence,
    (datetime, date): convert_datetime,
    Decimal: convert_decimal,
    uuid.UUID: convert_uuid,
    Enum: convert_enum,
}

# Add optional type converters if libraries are available
if NUMPY_AVAILABLE:
    TYPE_CONVERTERS.update(
        {
            (np.integer, np.floating): convert_numpy_number,
            np.ndarray: convert_numpy_array,
        }
    )

if PYDANTIC_AVAILABLE:
    TYPE_CONVERTERS[BaseModel] = convert_pydantic


def convert_for_protobuf(data: Any) -> Any:
    """Convert Python types to protobuf-compatible types."""
    if data is None:
        return None

    if isinstance(data, (str, int, float, bool)):
        return data

    # Find matching converter
    for types, converter in TYPE_CONVERTERS.items():
        if isinstance(data, types):
            return converter(data)

    # Default fallback
    return str(data)
