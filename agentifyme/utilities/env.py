import os
import re


def load_env_file(file_path: str):
    """Load environment variables from a file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"{file_path} does not exist.")

    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line and not line.startswith("#"):
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()

                # Remove surrounding quotes if present
                value = re.sub(r'^["\'](.*)["\']$', r"\1", value)

                os.environ[key] = value
