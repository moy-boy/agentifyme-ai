import base64
import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import Enum

import numpy as np
from pydantic import BaseModel


def generate_short_uuid():
    # Generate UUID bytes
    uuid_bytes = uuid.uuid4().bytes
    # Encode to base64 and clean up the string
    short = base64.urlsafe_b64encode(uuid_bytes).decode("ascii")
    return short.rstrip("=")


def get_message_id():
    return f"msg_{generate_short_uuid()}"


def get_run_id():
    return f"run_{generate_short_uuid()}"


def get_timestamp():
    return int(datetime.now().timestamp() * 1_000_000)


def convert_for_protobuf(data):
    """Convert Python types to protobuf-compatible types."""
    if data is None:
        return None

    if isinstance(data, (str, int, float, bool)):
        return data

    if isinstance(data, dict):
        return {k: convert_for_protobuf(v) for k, v in data.items()}

    if isinstance(data, (list, tuple, set)):
        return [convert_for_protobuf(v) for v in data]

    if isinstance(data, (datetime, date)):
        return data.isoformat()

    if isinstance(data, Decimal):
        return float(data)

    if isinstance(data, uuid.UUID):
        return str(data)

    if isinstance(data, Enum):
        return data.value

    if isinstance(data, (np.integer, np.floating)):
        return data.item()

    if isinstance(data, np.ndarray):
        return convert_for_protobuf(data.tolist())

    if isinstance(data, BaseModel):
        return convert_for_protobuf(data.model_dump())

    # if isinstance(data, pd.DataFrame):
    #     return convert_for_protobuf(data.to_dict("records"))

    # if isinstance(data, pd.Series):
    #     return convert_for_protobuf(data.to_dict())

    return str(data)
