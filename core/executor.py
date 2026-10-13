import config
from library import get_function
from core.voice import speak
from core.security import (
    is_risky_action,
    verify_system_permission,
    validate_parameters,
    request_double_confirmation,
)


def _emit(on_event, event: dict):
    """Notify UI or event listeners."""
    if on_event is not None:
        try:
            on_event(event)
        except Exception:
            pass


def _speak(message: str, on_event=None, wait: bool = False):
    """
    Safe voice emitter.
    Set wait=True to block execution until the sentence finishes speaking.
    """
    if not getattr(config, "VOICE_ENABLED", True) or not message:
        return

    try:
        # Calls speak with wait parameter to guarantee speech finishes first
        speak(str(message), wait=wait)
    except TypeError:
        # Fallback if your speak function does not yet accept wait
        speak(str(message))
    except Exception as error:
        _emit(on_event, {
            "stage": "voice_error",
            "message": str(error),
        })


def _error_result(name: str, message: str, definition: dict = None, execution_index: int = 0):
    return {
        "status": "error",
        "function": name,
        "execution_index": execution_index,
        "processing_command": definition.get("processing_command", "") if definition else "",
        "error": message,
    }


def execute(name: str, arguments: dict = None, on_event=None, confirm=None, execution_index: int = 0):
    """
    Execute a single registered function.
    Speaks the action first, waits for speech to complete, then runs the function.
    """
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Function name must be a non-empty string.")

    arguments = arguments or {}
    if not isinstance(arguments, dict):
        raise TypeError("Arguments must be a dictionary.")

    # 1. Lookup registered function
    try:
        definition = get_function(name)
    except (KeyError, LookupError):
        return _error_result(name, "Unknown function.", execution_index=execution_index)

    # 2. Check system policies
    allowed, perm_err = verify_system_permission(definition)
    if not allowed:
        return _error_result(name, perm_err, definition, execution_index=execution_index)

    # 3. Validate arguments against registry schema
    valid, param_err, inputs = validate_parameters(arguments, definition)
    if not valid:
        return _error_result(name, param_err, definition, execution_index=execution_index)

    # 4. Enforce security confirmation protocol if risky
    if is_risky_action(name, definition):
        confirmed, reason = request_double_confirmation(name, inputs, confirm)
        if not confirmed:
            msg = f"Action '{name}' cancelled: {reason}"
            _emit(on_event, {
                "stage": "confirmation_denied",
                "function": name,
                "execution_index": execution_index,
                "message": msg,
            })
            _speak("Action cancelled for security.", on_event, wait=False)
            return {
                "status": "cancelled",
                "function": name,
                "execution_index": execution_index,
                "executed": False,
                "message": msg,
            }

    # 5. Determine announcement text
    clean_action_name = name.replace("_", " ")
    processing = definition.get("processing_command", f"Processing {clean_action_name}...")
    
    # If definition['speak'] is empty, fall back to processing command
    pre_execution_speech = definition.get("speak") or processing

    _emit(on_event, {
        "stage": "executing",
        "message": processing,
        "function": name,
        "execution_index": execution_index,
        "inputs": inputs,
    })

    # Speak FIRST and wait until finished before executing the action
    _speak(pre_execution_speech, on_event, wait=True)

    # 6. Run the underlying action AFTER speaking finishes
    try:
        func = definition["function"]
        result = func(**inputs)

        # Format user response safely
        raw_response = definition.get("response", "Completed successfully: {result}")
        try:
            response = raw_response.format(**inputs, result=result)
        except Exception:
            response = f"Completed {clean_action_name}."

        output = {
            "status": "success",
            "function": name,
            "execution_index": execution_index,
            "inputs": inputs,
            "result": result,
            "response": response,
        }

        _emit(on_event, {
            "stage": "completed",
            "message": response,
            "execution_index": execution_index,
            "result": result,
        })

        # Speak completion message asynchronously
        _speak(response, on_event, wait=False)
        return output

    except Exception as error:
        err_msg = str(error)
        _emit(on_event, {
            "stage": "error",
            "message": err_msg,
            "function": name,
            "execution_index": execution_index,
        })
        _speak(f"Error while running {clean_action_name}: {err_msg}", on_event, wait=False)
        return _error_result(name, err_msg, definition, execution_index=execution_index)


def execute_all(intents_payload, on_event=None, confirm=None, stop_on_error: bool = True):
    """
    Execute multiple intents in sequence.
    """
    if isinstance(intents_payload, dict):
        intent_list = intents_payload.get("intents", [])
    elif isinstance(intents_payload, list):
        intent_list = intents_payload
    else:
        raise TypeError("intents_payload must be a dict or a list of intent objects.")

    results = []

    for idx, item in enumerate(intent_list):
        intent_name = item.get("intent")
        parameters = item.get("parameters", {})
        exec_idx = item.get("execution_index", idx)

        _emit(on_event, {
            "stage": "step_start",
            "step": idx + 1,
            "total_steps": len(intent_list),
            "function": intent_name,
        })

        result = execute(
            name=intent_name,
            arguments=parameters,
            on_event=on_event,
            confirm=confirm,
            execution_index=exec_idx,
        )
        results.append(result)

        if stop_on_error and result.get("status") in {"error", "cancelled"}:
            _emit(on_event, {
                "stage": "chain_aborted",
                "message": f"Execution halted at step {idx + 1} ({intent_name}).",
                "failed_step": exec_idx,
            })
            break

    return {
        "status": "completed" if all(r.get("status") == "success" for r in results) else "partial_or_failed",
        "results": results,
    }