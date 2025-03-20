#!/bin/bash
set -euo pipefail

PYTHON_LIB_PATH=$(find ${HOME}/.local/share/uv/python -name "libpython*.so*" -exec dirname {} \; | head -n 1)
if [ -n "$PYTHON_LIB_PATH" ]; then
  export LD_LIBRARY_PATH="$PYTHON_LIB_PATH:${LD_LIBRARY_PATH:-}"
else
  echo "Warning: Python library path not found"
fi

exec "$@"