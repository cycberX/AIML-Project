import os
import config

# Critical command blacklist / prefix list
RISKY_FUNCTION_NAMES = {
    "shutdown",
    "restart",
    "reboot",
    "delete_file",
    "delete_folder",
    "remove_file",
    "remove_folder",
    "kill_process",
    "format_drive",
    "execute_script",
}

RISKY_PREFIXES = (
    "delete_",
    "remove_",
    "shutdown_",
    "restart_",
    "format_",
    "kill_",
)


def is_risky_action(name: str, definition: dict) -> bool:
    """Determine whether an action requires explicit human confirmation."""
    risk_level = str(definition.get("risk_level", "")).lower()

    return (
        definition.get("confirmation_required", False)
        or risk_level in {"high", "critical"}
        or name in RISKY_FUNCTION_NAMES
        or name.startswith(RISKY_PREFIXES)
    )


def verify_system_permission(definition: dict) -> tuple[bool, str]:
    """Verify system-level category permissions defined in config."""
    if definition.get("category") == "system" and not getattr(
        config, "SYSTEM_FUNCTIONS_ENABLED", True
    ):
        return False, "System functions are disabled in config.py."
    return True, ""


def validate_parameters(arguments: dict, definition: dict) -> tuple[bool, str, dict]:
    """
    Validate presence of required parameters and reject unexpected keys.
    Returns: (is_valid, error_message, resolved_inputs)
    """
    parameters = definition.get("parameters", [])
    required = definition.get("required", [])

    if not isinstance(parameters, (list, tuple)) or not isinstance(required, (list, tuple)):
        return False, "Invalid function parameter metadata in registry.", {}

    missing = [key for key in required if key not in arguments]
    if missing:
        return False, f"Missing required parameters: {missing}", {}

    unexpected = set(arguments) - set(parameters)
    if unexpected:
        return False, f"Unexpected parameters: {sorted(unexpected)}", {}

    # Merge defaults with verified inputs
    resolved_inputs = {
        **definition.get("defaults", {}),
        **arguments,
    }
    return True, "", resolved_inputs


def request_double_confirmation(name: str, inputs: dict, confirm_cb) -> tuple[bool, str]:
    """
    Executes a 2-step verification protocol for high-risk actions.
    Returns: (confirmed: bool, reason: str)
    """
    if not callable(confirm_cb):
        return False, f"'{name}' is a risky action. A trusted confirmation callback is required."

    # Stage 1: Initial user intent confirmation
    first_ok = confirm_cb(
        f"Do you want to perform risky action '{name}' with arguments: {inputs}?",
        "yes",
    )
    if first_ok is not True:
        return False, "First confirmation declined."

    # Stage 2: Explicit challenge phrase verification
    challenge_phrase = f"CONFIRM {name.upper()}"
    second_ok = confirm_cb(
        f"Final confirmation: Type exactly '{challenge_phrase}' to execute.",
        challenge_phrase,
    )
    if second_ok is not True:
        return False, "Final verification phrase declined or mismatched."

    return True, "Confirmed."