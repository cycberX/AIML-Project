

from .math.functions import FUNCTIONS as MATH_FUNCTIONS
from .system.functions import FUNCTIONS as SYSTEM_FUNCTIONS
from .file_system.functions import FUNCTIONS as FILE_SYSTEM_FUNCTIONS

ALL_FUNCTIONS = (MATH_FUNCTIONS + SYSTEM_FUNCTIONS + FILE_SYSTEM_FUNCTIONS)

FUNCTION_MAP = {
    item["name"]: item
    for item in ALL_FUNCTIONS
}


def get_function_list():
    """Return metadata suitable for JSON and ML training."""
    return [
        {
            key: value
            for key, value in item.items()
            if key != "function"
        }
        for item in ALL_FUNCTIONS
    ]


def get_function(name):
    if name not in FUNCTION_MAP:
        raise ValueError(f"Unknown function: {name}")
    return FUNCTION_MAP[name]
