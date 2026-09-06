def normalize_output(text: str) -> str:
    """Unify newlines and drop trailing whitespace so extra final newlines do not fail tests."""
    return text.replace("\r\n", "\n").replace("\r", "\n").rstrip()
