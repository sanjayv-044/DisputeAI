
import re


def filter_sensitive_output(text):
    """Mask common sensitive information in investigation reports."""

    # Mask 6-digit OTP-like values
    text = re.sub(
        r"\b\d{6}\b",
        "[REDACTED OTP/PIN]",
        text
    )

    # Mask common 16-digit card numbers
    text = re.sub(
        r"\b(?:\d[ -]?){15}\d\b",
        "[REDACTED CARD NUMBER]",
        text
    )

    # Mask email addresses
    text = re.sub(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        "[REDACTED EMAIL]",
        text
    )

    return text


print("Output security module created successfully!")
