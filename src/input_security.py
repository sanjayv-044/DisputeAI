
import re

INJECTION_PATTERNS = [
    r"ignore all previous instructions",
    r"ignore previous instructions",
    r"reveal system prompt",
    r"reveal confidential information",
    r"bypass security",
    r"disregard your instructions",
    r"act as system"
]


def check_input_security(user_input):
    """Detect common prompt injection indicators."""

    text = user_input.lower()

    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text):
            return {
                "safe": False,
                "message": "Potential prompt injection detected."
            }

    return {
        "safe": True,
        "message": "Input passed basic security checks."
    }


print("Input security module created successfully!")
