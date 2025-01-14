import base64
import uuid
from datetime import datetime


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
