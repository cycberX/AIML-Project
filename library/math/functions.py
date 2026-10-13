
import math


def add(numbers):
    return sum(numbers)


def subtract(a, b):
    return a - b


def multiply(numbers):
    return math.prod(numbers)


def divide(a, b):
    if b == 0:
        raise ZeroDivisionError("Cannot divide by zero")
    return a / b


def modulo(a, b):
    if b == 0:
        raise ZeroDivisionError("Cannot calculate modulo by zero")
    return a % b


def power(a, b):
    return a ** b


def floor_divide(a, b):
    if b == 0:
        raise ZeroDivisionError("Cannot divide by zero")
    return a // b


def square(a):
    return a ** 2


def cube(a):
    return a ** 3


def square_root(a):
    if a < 0:
        raise ValueError("Square root requires a non-negative number")
    return math.sqrt(a)


def cube_root(a):
    return math.copysign(abs(a) ** (1 / 3), a)


def absolute(a):
    return abs(a)


def factorial(n):
    if isinstance(n, bool) or not isinstance(n, int) or n < 0:
        raise ValueError("Factorial requires a non-negative integer")
    return math.factorial(n)


def average(numbers):
    if not numbers:
        raise ValueError("At least one number is required")
    return sum(numbers) / len(numbers)


def minimum(numbers):
    if not numbers:
        raise ValueError("At least one number is required")
    return min(numbers)


def maximum(numbers):
    if not numbers:
        raise ValueError("At least one number is required")
    return max(numbers)


def round_number(number, digits=0):
    return round(number, digits)


def percentage(number, percent):
    return number * percent / 100


def percentage_change(old, new):
    if old == 0:
        raise ZeroDivisionError("Original value cannot be zero")
    return (new - old) / abs(old) * 100


def gcd(a, b):
    return math.gcd(a, b)


def lcm(a, b):
    return math.lcm(a, b)


def is_prime(n):
    if isinstance(n, bool) or not isinstance(n, int):
        raise TypeError("An integer is required")
    if n < 2:
        return False
    return all(n % d != 0 for d in range(2, math.isqrt(n) + 1))


def is_even(n):
    return n % 2 == 0


def is_odd(n):
    return n % 2 != 0


def greater_than(a, b):
    return a > b


def less_than(a, b):
    return a < b


def equal(a, b):
    return a == b


def logical_and(a, b):
    return bool(a) and bool(b)


def logical_or(a, b):
    return bool(a) or bool(b)


def logical_not(a):
    return not bool(a)


def logical_xor(a, b):
    return bool(a) != bool(b)


def sine(angle):
    return math.sin(angle)


def cosine(angle):
    return math.cos(angle)


def logarithm(number, base=math.e):
    if number <= 0 or base <= 0 or base == 1:
        raise ValueError("Invalid logarithm arguments")
    return math.log(number, base)


def clamp(number, minimum_value, maximum_value):
    if minimum_value > maximum_value:
        raise ValueError("Minimum cannot exceed maximum")
    return max(minimum_value, min(number, maximum_value))


def degrees_to_radians(angle):
    return math.radians(angle)


def radians_to_degrees(angle):
    return math.degrees(angle)


# Function metadata lives beside the actual math functions.
# The registry imports this list; the execution environment
# uses it to control the processing flow.

FUNCTIONS = [
    {
        "name": "add",
        "function": add,
        "parameters": ["numbers"],
        "required": ["numbers"],
        "processing_command": "math.add",
        "speak": "Adding the given numbers. Please wait.",
        "response": "The sum of {numbers} is {result}.",
    },
    {
        "name": "subtract",
        "function": subtract,
        "parameters": ["a", "b"],
        "required": ["a", "b"],
        "processing_command": "math.subtract",
        "speak": "Subtracting the second number from the first.",
        "response": "{a} minus {b} equals {result}.",
    },
    {
        "name": "multiply",
        "function": multiply,
        "parameters": ["numbers"],
        "required": ["numbers"],
        "processing_command": "math.multiply",
        "speak": "Multiplying the given numbers. Please wait.",
        "response": "The product of {numbers} is {result}.",
    },
    {
        "name": "divide",
        "function": divide,
        "parameters": ["a", "b"],
        "required": ["a", "b"],
        "processing_command": "math.divide",
        "speak": "Dividing the first number by the second.",
        "response": "{a} divided by {b} equals {result}.",
    },
    {
        "name": "modulo",
        "function": modulo,
        "parameters": ["a", "b"],
        "required": ["a", "b"],
        "processing_command": "math.modulo",
        "speak": "Calculating the division remainder.",
        "response": "The remainder of {a} divided by {b} is {result}.",
    },
    {
        "name": "power",
        "function": power,
        "parameters": ["a", "b"],
        "required": ["a", "b"],
        "processing_command": "math.power",
        "speak": "Calculating the power of the given number.",
        "response": "{a} raised to power {b} equals {result}.",
    },
    {
        "name": "floor_divide",
        "function": floor_divide,
        "parameters": ["a", "b"],
        "required": ["a", "b"],
        "processing_command": "math.floor_divide",
        "speak": "Performing floor division.",
        "response": "The floor division result is {result}.",
    },
    {
        "name": "square",
        "function": square,
        "parameters": ["a"],
        "required": ["a"],
        "processing_command": "math.square",
        "speak": "Calculating the square.",
        "response": "The square of {a} is {result}.",
    },
    {
        "name": "cube",
        "function": cube,
        "parameters": ["a"],
        "required": ["a"],
        "processing_command": "math.cube",
        "speak": "Calculating the cube.",
        "response": "The cube of {a} is {result}.",
    },
    {
        "name": "square_root",
        "function": square_root,
        "parameters": ["a"],
        "required": ["a"],
        "processing_command": "math.square_root",
        "speak": "Calculating the square root.",
        "response": "The square root of {a} is {result}.",
    },
    {
        "name": "cube_root",
        "function": cube_root,
        "parameters": ["a"],
        "required": ["a"],
        "processing_command": "math.cube_root",
        "speak": "Calculating the cube root.",
        "response": "The cube root of {a} is {result}.",
    },
    {
        "name": "absolute",
        "function": absolute,
        "parameters": ["a"],
        "required": ["a"],
        "processing_command": "math.absolute",
        "speak": "Finding the absolute value.",
        "response": "The absolute value of {a} is {result}.",
    },
    {
        "name": "factorial",
        "function": factorial,
        "parameters": ["n"],
        "required": ["n"],
        "processing_command": "math.factorial",
        "speak": "Calculating the factorial.",
        "response": "The factorial of {n} is {result}.",
    },
    {
        "name": "average",
        "function": average,
        "parameters": ["numbers"],
        "required": ["numbers"],
        "processing_command": "math.average",
        "speak": "Calculating the average.",
        "response": "The average of {numbers} is {result}.",
    },
    {
        "name": "minimum",
        "function": minimum,
        "parameters": ["numbers"],
        "required": ["numbers"],
        "processing_command": "math.minimum",
        "speak": "Finding the smallest number.",
        "response": "The smallest number is {result}.",
    },
    {
        "name": "maximum",
        "function": maximum,
        "parameters": ["numbers"],
        "required": ["numbers"],
        "processing_command": "math.maximum",
        "speak": "Finding the largest number.",
        "response": "The largest number is {result}.",
    },
    {
        "name": "round_number",
        "function": round_number,
        "parameters": ["number", "digits"],
        "required": ["number"],
        "defaults": {"digits": 0},
        "processing_command": "math.round",
        "speak": "Rounding the given number.",
        "response": "The rounded value is {result}.",
    },
    {
        "name": "percentage",
        "function": percentage,
        "parameters": ["number", "percent"],
        "required": ["number", "percent"],
        "processing_command": "math.percentage",
        "speak": "Calculating the requested percentage.",
        "response": "{percent} percent of {number} is {result}.",
    },
    {
        "name": "percentage_change",
        "function": percentage_change,
        "parameters": ["old", "new"],
        "required": ["old", "new"],
        "processing_command": "math.percentage_change",
        "speak": "Calculating the percentage change.",
        "response": "The percentage change is {result} percent.",
    },
    {
        "name": "gcd",
        "function": gcd,
        "parameters": ["a", "b"],
        "required": ["a", "b"],
        "processing_command": "math.gcd",
        "speak": "Finding the greatest common divisor.",
        "response": "The greatest common divisor is {result}.",
    },
    {
        "name": "lcm",
        "function": lcm,
        "parameters": ["a", "b"],
        "required": ["a", "b"],
        "processing_command": "math.lcm",
        "speak": "Finding the least common multiple.",
        "response": "The least common multiple is {result}.",
    },
    {
        "name": "is_prime",
        "function": is_prime,
        "parameters": ["n"],
        "required": ["n"],
        "processing_command": "math.is_prime",
        "speak": "Checking whether the number is prime.",
        "response": "Is {n} a prime number? {result}.",
    },
    {
        "name": "is_even",
        "function": is_even,
        "parameters": ["n"],
        "required": ["n"],
        "processing_command": "math.is_even",
        "speak": "Checking whether the number is even.",
        "response": "Is {n} even? {result}.",
    },
    {
        "name": "is_odd",
        "function": is_odd,
        "parameters": ["n"],
        "required": ["n"],
        "processing_command": "math.is_odd",
        "speak": "Checking whether the number is odd.",
        "response": "Is {n} odd? {result}.",
    },
    {
        "name": "greater_than",
        "function": greater_than,
        "parameters": ["a", "b"],
        "required": ["a", "b"],
        "processing_command": "math.greater_than",
        "speak": "Comparing the two numbers.",
        "response": "Is {a} greater than {b}? {result}.",
    },
    {
        "name": "less_than",
        "function": less_than,
        "parameters": ["a", "b"],
        "required": ["a", "b"],
        "processing_command": "math.less_than",
        "speak": "Comparing the two numbers.",
        "response": "Is {a} less than {b}? {result}.",
    },
    {
        "name": "equal",
        "function": equal,
        "parameters": ["a", "b"],
        "required": ["a", "b"],
        "processing_command": "math.equal",
        "speak": "Checking whether the values are equal.",
        "response": "Are {a} and {b} equal? {result}.",
    },
    {
        "name": "logical_and",
        "function": logical_and,
        "parameters": ["a", "b"],
        "required": ["a", "b"],
        "processing_command": "math.logical_and",
        "speak": "Executing the logical AND operation.",
        "response": "The logical AND result is {result}.",
    },
    {
        "name": "logical_or",
        "function": logical_or,
        "parameters": ["a", "b"],
        "required": ["a", "b"],
        "processing_command": "math.logical_or",
        "speak": "Executing the logical OR operation.",
        "response": "The logical OR result is {result}.",
    },
    {
        "name": "logical_not",
        "function": logical_not,
        "parameters": ["a"],
        "required": ["a"],
        "processing_command": "math.logical_not",
        "speak": "Inverting the logical value.",
        "response": "The logical NOT result is {result}.",
    },
    {
        "name": "logical_xor",
        "function": logical_xor,
        "parameters": ["a", "b"],
        "required": ["a", "b"],
        "processing_command": "math.logical_xor",
        "speak": "Executing the exclusive OR operation.",
        "response": "The logical XOR result is {result}.",
    },
    {
        "name": "sine",
        "function": sine,
        "parameters": ["angle"],
        "required": ["angle"],
        "processing_command": "math.sine",
        "speak": "Calculating sine in radians.",
        "response": "The sine of {angle} radians is {result}.",
    },
    {
        "name": "cosine",
        "function": cosine,
        "parameters": ["angle"],
        "required": ["angle"],
        "processing_command": "math.cosine",
        "speak": "Calculating cosine in radians.",
        "response": "The cosine of {angle} radians is {result}.",
    },
    {
        "name": "logarithm",
        "function": logarithm,
        "parameters": ["number", "base"],
        "required": ["number"],
        "defaults": {"base": math.e},
        "processing_command": "math.logarithm",
        "speak": "Calculating the logarithm.",
        "response": "The logarithm of {number} with base {base} is {result}.",
    },
    {
        "name": "clamp",
        "function": clamp,
        "parameters": ["number", "minimum_value", "maximum_value"],
        "required": ["number", "minimum_value", "maximum_value"],
        "processing_command": "math.clamp",
        "speak": "Restricting the number to the specified range.",
        "response": "The value within the range is {result}.",
    },
    {
        "name": "degrees_to_radians",
        "function": degrees_to_radians,
        "parameters": ["angle"],
        "required": ["angle"],
        "processing_command": "math.degrees_to_radians",
        "speak": "Converting degrees to radians.",
        "response": "{angle} degrees equals {result} radians.",
    },
    {
        "name": "radians_to_degrees",
        "function": radians_to_degrees,
        "parameters": ["angle"],
        "required": ["angle"],
        "processing_command": "math.radians_to_degrees",
        "speak": "Converting radians to degrees.",
        "response": "{angle} radians equals {result} degrees.",
    },
]
