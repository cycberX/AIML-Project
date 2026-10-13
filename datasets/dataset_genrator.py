import json
import random
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

OUTPUT_FILE = PROJECT_ROOT / "datasets" / "training_dataset.json"
TARGET_SIZE = 100_000
RANDOM_SEED = 42
MAX_INTENTS_PER_EXAMPLE = 3
MAX_GENERATION_ATTEMPTS = TARGET_SIZE * 50

random.seed(RANDOM_SEED)

from library import get_function_list


# For common intents, use phrases that users are likely to say.
# Other registered functions are generated from their registry names.
INTENT_PHRASES = {
    "add": ["add", "sum", "calculate the sum of"],
    "subtract": ["subtract", "take away", "calculate the difference between"],
    "multiply": ["multiply", "times", "calculate the product of"],
    "divide": ["divide", "calculate the quotient of"],
    "modulo": ["find the remainder of", "calculate the modulo of"],
    "power": ["raise to the power", "calculate the power of"],
    "square": ["square", "calculate the square of"],
    "cube": ["cube", "calculate the cube of"],
    "square_root": ["find the square root of", "calculate the square root of"],
    "cube_root": ["find the cube root of", "calculate the cube root of"],
    "absolute": ["find the absolute value of", "calculate the absolute value of"],
    "factorial": ["calculate the factorial of", "find the factorial of"],
    "average": ["calculate the average of", "find the mean of"],
    "minimum": ["find the smallest value in", "find the minimum of"],
    "maximum": ["find the largest value in", "find the maximum of"],
    "round_number": ["round", "round the number"],
    "percentage": ["calculate the percentage", "find the percentage"],
    "percentage_change": ["calculate the percentage change", "find the percentage change"],
    "gcd": ["find the greatest common divisor of", "calculate the GCD of"],
    "lcm": ["find the least common multiple of", "calculate the LCM of"],
    "is_prime": ["check whether is prime", "is this number prime"],
    "is_even": ["check whether is even", "is this number even"],
    "is_odd": ["check whether is odd", "is this number odd"],
    "greater_than": ["check whether is greater than", "compare if is greater than"],
    "less_than": ["check whether is less than", "compare if is less than"],
    "equal": ["check whether these values are equal", "compare these values"],
    "logical_and": ["perform logical AND on", "calculate logical AND for"],
    "logical_or": ["perform logical OR on", "calculate logical OR for"],
    "logical_not": ["perform logical NOT on", "invert the logical value"],
    "logical_xor": ["perform logical XOR on", "calculate exclusive OR for"],
    "sine": ["calculate the sine of", "find sin"],
    "cosine": ["calculate the cosine of", "find cos"],
    "logarithm": ["calculate the logarithm of", "find the log of"],
    "clamp": ["clamp", "limit to the range"],
    "degrees_to_radians": ["convert degrees to radians for", "convert to radians"],
    "radians_to_degrees": ["convert radians to degrees for", "convert to degrees"],
    "sleep": ["sleep", "wait"],
    "get_time": ["get the current time", "tell me the current time"],
    "get_date": ["get today's date", "tell me the current date"],
    "get_datetime": ["get the current date and time", "tell me the date and time"],
    "increase_volume": ["increase the volume", "turn the volume up", "raise the volume"],
    "decrease_volume": ["decrease the volume", "turn the volume down", "lower the volume"],
    "set_volume": ["set the volume to", "change the volume to"],
    "mute_volume": ["mute the volume", "mute the sound"],
    "unmute_volume": ["unmute the volume", "turn the sound back on"],
    "increase_brightness": ["increase the brightness", "make the screen brighter"],
    "decrease_brightness": ["decrease the brightness", "dim the screen"],
    "set_brightness": ["set the brightness to", "change the brightness to"],
    "open_settings": ["open settings", "launch system settings"],
    "lock_workstation": ["lock the computer", "lock this workstation"],
    "create_file": ["create a file", "make a new file"],
    "delete_file": ["delete the file", "remove the file"],
    "rename_file": ["rename the file", "change the file name"],
    "find_file": ["find the file", "search for the file"],
    "create_folder": ["create a folder", "make a new folder"],
    "delete_folder": ["delete the folder", "remove the folder"],
    "rename_folder": ["rename the folder", "change the folder name"],
    "find_folder": ["find the folder", "search for the folder"],
    "list_directory": ["list the files in the folder", "show the folder contents"],
}

PARAMETER_PHRASES = {
    "a": ["first number", "a"],
    "b": ["second number", "b"],
    "n": ["number"],
    "numbers": ["numbers"],
    "number": ["number"],
    "old": ["old value"],
    "new": ["new value"],
    "percent": ["percent"],
    "base": ["base"],
    "angle": ["angle"],
    "digits": ["decimal places"],
    "seconds": ["seconds"],
    "level": ["level"],
    "value": ["value"],
    "step": ["step"],
    "steps": ["steps"],
    "path": ["path"],
    "name": ["name"],
    "filename": ["file name"],
    "foldername": ["folder name"],
    "new_name": ["new name"],
    "content": ["content"],
    "overwrite": ["overwrite"],
    "max_bytes": ["maximum bytes"],
    "start_path": ["starting path"],
    "destination_folder": ["destination folder"],
    "interface": ["network interface"],
    "profile": ["network profile"],
    "minimum": ["minimum"],
    "maximum": ["maximum"],
    "minimum_value": ["minimum value"],
    "maximum_value": ["maximum value"],
    "enabled": ["enabled"],
    "state": ["state"],
    "flag": ["flag"],
    "destination": ["destination"],
    "source": ["source"],
}


FILE_NAMES = [
    "notes.txt", "report.txt", "config.json", "data.json",
    "output.txt", "example.py", "document.md", "backup.txt",
    "todo.txt", "summary.txt", "results.csv", "settings.json",
]
FOLDER_NAMES = [
    "documents", "reports", "projects", "backup", "test_folder",
    "downloads", "work", "notes", "archive",
]
TEXT_CONTENTS = [
    "Hello World", "Sample text", "Training dataset example",
    "This is a test file", "Meeting notes", "Project report",
]
JOINERS = [
    " and then ", ", then ", " and after that ",
    ". After that, ", ", followed by ", " and ",
]


def load_commands():
    definitions = get_function_list()
    if isinstance(definitions, dict):
        definitions = list(definitions.values())

    commands = {}
    for definition in definitions:
        if not isinstance(definition, dict):
            continue
        name = definition.get("name")
        if not name:
            continue

        parameters = definition.get("parameters", [])
        required = definition.get("required", [])
        defaults = definition.get("defaults", {})

        # Accommodate registry schemas that store parameter definitions as
        # dictionaries, although the common project format uses names.
        if isinstance(parameters, dict):
            parameter_names = list(parameters.keys())
        else:
            parameter_names = []
            for parameter in parameters:
                if isinstance(parameter, str):
                    parameter_names.append(parameter)
                elif isinstance(parameter, dict) and parameter.get("name"):
                    parameter_names.append(parameter["name"])

        commands[name] = {
            "parameters": parameter_names,
            "required": list(required),
            "defaults": dict(defaults) if isinstance(defaults, dict) else {},
            "category": definition.get("category", "general"),
        }

    if not commands:
        raise RuntimeError(
            "No registered functions found. Check library.get_function_list()."
        )

    for name, definition in commands.items():
        unknown_required = set(definition["required"]) - set(definition["parameters"])
        if unknown_required:
            raise ValueError(
                f"{name}: required parameters absent from parameters list: "
                f"{sorted(unknown_required)}"
            )
    return commands


COMMANDS = load_commands()


def random_number():
    return random.randint(-100, 100)


def generate_value(parameter, intent_name, defaults):
    """Generate a plausible typed value based on parameter name/default."""
    key = parameter.lower()

    if key in {"numbers", "values", "items"}:
        return [random_number(), random_number(), random_number()]
    if key in {"a", "b", "x", "y"}:
        if intent_name.startswith("logical_"):
            return random.choice([True, False])
        if key == "b" and intent_name in {"divide", "modulo", "floor_divide"}:
            return random.choice([n for n in range(-100, 101) if n != 0])
        if intent_name == "power" and key == "b":
            return random.randint(0, 5)
        return random_number()
    if key in {"n"}:
        return random.randint(0, 12) if intent_name == "factorial" else random.randint(0, 1000)
    if key in {"seconds", "duration", "timeout"}:
        return random.choice([1, 2, 5, 10, 15, 30, 45, 60])
    if key in {"digits", "decimal_places"}:
        return random.randint(0, 5)
    if key in {"percent", "percentage"}:
        return random.randint(1, 100)
    if key in {"base"}:
        return random.choice([2, 10, 2.718281828459045])
    if key in {"angle"}:
        return random.randint(0, 360)
    if key in {"level", "brightness", "volume", "value", "amount", "step", "steps"}:
        return random.choice([1, 5, 10, 15, 20, 25, 40, 50, 70, 80, 90, 100])
    if key in {"minimum_value", "maximum_value", "minimum", "maximum", "min_value", "max_value"}:
        return random.randint(0, 100)
    if key in {"old", "new", "number"}:
        return random.randint(1, 1000)
    if key in {"enabled", "state", "flag", "overwrite", "recursive", "hidden"}:
        return random.choice([True, False])
    if key in {"path", "start_path", "source", "destination"}:
        return random.choice([".", *FILE_NAMES])
    if key in {"name", "filename", "file_name", "file"}:
        if "folder" in intent_name:
            return random.choice(FOLDER_NAMES)
        return random.choice(FILE_NAMES)
    if key in {"folder", "foldername", "folder_name", "directory"}:
        return random.choice(FOLDER_NAMES)
    if key in {"new_name", "new_filename", "new_file_name"}:
        return random.choice(FILE_NAMES)
    if key in {"destination_folder", "folder_path"}:
        return random.choice(FOLDER_NAMES)
    if key in {"content", "text", "data"}:
        return random.choice(TEXT_CONTENTS)
    if key in {"interface"}:
        return random.choice(["Wi-Fi", "Ethernet"])
    if key in {"profile"}:
        return random.choice(["HomeWiFi", "OfficeWiFi", "MyNetwork"])
    if key in {"max_bytes"}:
        return random.choice([1000, 10000, 100000, 1000000])

    # Preserve the type of a registry default whenever available.
    if parameter in defaults:
        default = defaults[parameter]
        if isinstance(default, bool):
            return random.choice([True, False])
        if isinstance(default, int) and not isinstance(default, bool):
            return random.randint(max(-100, default - 20), min(1000, default + 20))
        if isinstance(default, float):
            return round(random.uniform(max(0, default - 10), default + 10), 2)
        if isinstance(default, list):
            return list(default)
        if isinstance(default, str):
            return default or random.choice(["example", "sample", "default"])
        return default

    # Avoid guessing arbitrary non-string types for unknown registry fields.
    return "example"


def generate_parameters(name, definition):
    """Generate required parameters and occasionally include optional ones."""
    required = set(definition["required"])
    optional = [
        parameter for parameter in definition["parameters"]
        if parameter not in required
    ]

    # Most samples contain only required parameters. Some include optional
    # parameters to teach the model how optional arguments are expressed.
    selected = list(definition["required"])
    for parameter in optional:
        if random.random() < 0.25:
            selected.append(parameter)

    defaults = definition["defaults"]
    parameters = {
        parameter: generate_value(parameter, name, defaults)
        for parameter in selected
    }

    # Fix known semantic constraints.
    if name == "clamp":
        low_key = "minimum_value" if "minimum_value" in parameters else "minimum"
        high_key = "maximum_value" if "maximum_value" in parameters else "maximum"
        if low_key in parameters and high_key in parameters:
            low, high = sorted((parameters[low_key], parameters[high_key]))
            parameters[low_key], parameters[high_key] = low, high

    if name in {"divide", "modulo", "floor_divide"} and parameters.get("b") == 0:
        parameters["b"] = 1

    missing = required - set(parameters)
    unexpected = set(parameters) - set(definition["parameters"])
    if missing or unexpected:
        raise ValueError(
            f"{name}: missing={sorted(missing)}, unexpected={sorted(unexpected)}"
        )
    return parameters


def value_text(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        return ", ".join(value_text(item) for item in value)
    return str(value)


def phrase_for(name):
    phrases = INTENT_PHRASES.get(name)
    if phrases:
        return random.choice(phrases)
    return name.replace("_", " ")


def parameter_fragments(parameters):
    fragments = []
    for key, value in parameters.items():
        label_options = PARAMETER_PHRASES.get(key, [key.replace("_", " ")])
        label = random.choice(label_options)
        fragments.append((key, label, value))
    return fragments


def make_prompt(name, parameters, category):
    """Create a prompt that contains the intent and the generated values."""
    phrase = phrase_for(name)
    params = parameter_fragments(parameters)

    # A few known intents have natural word order and should not be rendered
    # as generic "parameter name=value" prompts.
    if name in {"add", "multiply", "average", "minimum", "maximum"} and "numbers" in parameters:
        numbers = value_text(parameters["numbers"])
        return random.choice([
            f"{phrase} {numbers}",
            f"please {phrase} {numbers}",
            f"what is the result when I {phrase} {numbers}?",
        ])

    if name in {"subtract", "divide", "modulo", "power", "greater_than", "less_than", "equal"}:
        if "a" in parameters and "b" in parameters:
            a, b = value_text(parameters["a"]), value_text(parameters["b"])
            patterns = {
                "subtract": [f"subtract {b} from {a}", f"what is {a} minus {b}?"],
                "divide": [f"divide {a} by {b}", f"what is {a} divided by {b}?"],
                "modulo": [f"find the remainder when {a} is divided by {b}", f"{a} modulo {b}"],
                "power": [f"calculate {a} to the power of {b}", f"raise {a} to power {b}"],
                "greater_than": [f"is {a} greater than {b}?", f"check whether {a} is greater than {b}"],
                "less_than": [f"is {a} less than {b}?", f"check whether {a} is less than {b}"],
                "equal": [f"are {a} and {b} equal?", f"check whether {a} equals {b}"],
            }
            rendered = random.choice(patterns[name])
            extras = [
                (key, label, value) for key, label, value in params
                if key not in {"a", "b"}
            ]
            if extras:
                rendered += " " + " ".join(
                    f"{label} {value_text(value)}" for _, label, value in extras
                )
            return rendered

    # For all remaining intents, state the action clearly and include every
    # generated argument value so parameter labels and values remain aligned.
    if not params:
        category_suffix = {
            "system": " on the computer",
            "filesystem": " in the allowed folder",
        }.get(category, "")
        return random.choice([
            f"{phrase}{category_suffix}",
            f"please {phrase}{category_suffix}",
            f"can you {phrase}{category_suffix}?",
            f"I want to {phrase}{category_suffix}",
        ])

    rendered_params = []
    for _, label, value in params:
        rendered_params.append(f"{label} {value_text(value)}")
    parameter_text = ", ".join(rendered_params)

    if category == "filesystem":
        suffix = " in the allowed folder"
    elif category == "system":
        suffix = " on the computer"
    else:
        suffix = ""

    return random.choice([
        f"{phrase} {parameter_text}{suffix}",
        f"please {phrase} with {parameter_text}{suffix}",
        f"can you {phrase} using {parameter_text}{suffix}?",
        f"I want to {phrase} {parameter_text}{suffix}",
        f"{phrase.capitalize()}: {parameter_text}{suffix}",
    ])


def make_intent(name, index):
    definition = COMMANDS[name]
    parameters = generate_parameters(name, definition)
    prompt = make_prompt(name, parameters, definition["category"])
    return prompt, {
        "index": index,
        "intent": name,
        "parameters": parameters,
        "execution_index": index,
    }


def generate_example(example_id):
    names = list(COMMANDS)
    count = random.choices(
        list(range(1, MAX_INTENTS_PER_EXAMPLE + 1)),
        weights=[45, 40, 15][:MAX_INTENTS_PER_EXAMPLE],
        k=1,
    )[0]
    count = min(count, len(names))
    selected_names = random.sample(names, k=count)

    prompt_parts = []
    intents = []
    for index, name in enumerate(selected_names):
        part, intent = make_intent(name, index)
        prompt_parts.append(part)
        intents.append(intent)

    combined_prompt = prompt_parts[0]
    for part in prompt_parts[1:]:
        combined_prompt += random.choice(JOINERS) + part

    return {
        "id": example_id,
        "input": combined_prompt,
        "output": {"intents": intents},
    }


def validate_example(example):
    if not isinstance(example, dict) or not isinstance(example.get("input"), str):
        raise ValueError("Example must have a string 'input'.")
    intents = example.get("output", {}).get("intents")
    if not isinstance(intents, list) or not intents:
        raise ValueError("Example must contain a non-empty output.intents list.")

    for index, item in enumerate(intents):
        name = item.get("intent")
        if name not in COMMANDS:
            raise ValueError(f"Unknown intent: {name}")
        if item.get("index") != index or item.get("execution_index") != index:
            raise ValueError(f"{name}: incorrect index/execution_index.")
        params = item.get("parameters")
        if not isinstance(params, dict):
            raise ValueError(f"{name}: parameters must be an object.")
        definition = COMMANDS[name]
        missing = set(definition["required"]) - set(params)
        unexpected = set(params) - set(definition["parameters"])
        if missing or unexpected:
            raise ValueError(
                f"{name}: missing={sorted(missing)}, unexpected={sorted(unexpected)}"
            )


def main():
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    examples = []
    seen_prompts = set()
    attempts = 0

    while len(examples) < TARGET_SIZE:
        attempts += 1
        if attempts > MAX_GENERATION_ATTEMPTS:
            raise RuntimeError(
                f"Only generated {len(examples)} unique prompts after "
                f"{attempts} attempts. Add more phrase variations."
            )

        example = generate_example(len(examples) + 1)
        normalized = " ".join(example["input"].casefold().split())
        if normalized in seen_prompts:
            continue

        validate_example(example)
        seen_prompts.add(normalized)
        examples.append(example)

        if len(examples) % 10_000 == 0:
            print(f"Generated {len(examples):,}/{TARGET_SIZE:,} examples...")

    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(examples, file, indent=2, ensure_ascii=False)

    print("=" * 60)
    print("DATASET GENERATION COMPLETED")
    print("=" * 60)
    print(f"Output file: {OUTPUT_FILE}")
    print(f"Total examples: {len(examples):,}")
    print(f"Registered functions: {len(COMMANDS)}")
    print(f"Unique prompts: {len(seen_prompts):,}")
    print(f"Generation attempts: {attempts:,}")
    print("Output schema: input + output.intents[] (intent, parameters, order)")
    print("=" * 60)


if __name__ == "__main__":
    main()

