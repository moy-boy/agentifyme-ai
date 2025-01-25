import importlib
import os
import pkgutil
import sys
from typing import Any

from loguru import logger


def find_package_directories(root_dir: str) -> list[str]:
    """Recursively find all directories that contain Python files, ignoring hidden directories."""
    src_dir = os.path.join(root_dir, "src")
    base_dir = src_dir if os.path.exists(src_dir) else root_dir

    package_dirs = []
    for root, dirs, files in os.walk(base_dir):
        # Remove hidden directories and .venv from dirs to prevent os.walk from traversing them
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != ".venv"]

        if any(file.endswith(".py") for file in files):
            rel_path = os.path.relpath(root, base_dir)
            if rel_path != ".":
                package_dirs.append(rel_path.replace(os.path.sep, "."))
    return package_dirs


def setup_dynamic_packages(root_dir: str) -> list[str]:
    """Set up multiple dynamic packages for importing."""
    src_dir = os.path.join(root_dir, "src")
    base_dir = src_dir if os.path.exists(src_dir) else root_dir
    package_names = find_package_directories(root_dir)

    if not package_names:
        raise ValueError("No packages containing Python files found.")

    # Add the base directory to sys.path
    if base_dir not in sys.path:
        sys.path.insert(0, base_dir)

    return package_names


def list_modules(package_name: str) -> list[str]:
    """List all modules in a package."""
    package = importlib.import_module(package_name)
    return [name for _, name, _ in pkgutil.iter_modules(package.__path__)]


def import_module(package_name: str, module_name: str) -> Any:
    """Dynamically import a module from a package."""
    try:
        return importlib.import_module(f"{package_name}.{module_name}")
    except ImportError as e:
        logger.error(f"Error importing module '{module_name}' from package '{package_name}': {e}")
        return None


def load_modules_from_directory(root_dir: str) -> dict[str, dict[str, Any]]:
    """Load Python modules from the root directory or src directory if it exists.

    Args:
        root_dir (str): The root directory of the project.

    Returns:
        Dict[str, Dict[str, Any]]: A dictionary of loaded modules, organized by package.

    """
    src_dir = os.path.join(root_dir, "src")
    base_dir = src_dir if os.path.exists(src_dir) else root_dir

    try:
        package_names = setup_dynamic_packages(base_dir)

        loaded_modules: dict[str, dict[str, Any]] = {}

        for package_name in package_names:
            modules = list_modules(package_name)
            loaded_modules[package_name] = {}

            for module_name in modules:
                module = import_module(package_name, module_name)
                if module:
                    loaded_modules[package_name][module_name] = module

        return loaded_modules
    except ValueError as e:
        logger.error("Error loading modules from directory", exc_info=True, error=str(e))

    return {}
