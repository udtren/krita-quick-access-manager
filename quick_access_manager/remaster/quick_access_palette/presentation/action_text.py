"""Helpers for converting Krita/Qt action text into palette display text."""


def display_action_text(text: str) -> str:
    """Remove Qt mnemonic markers while preserving escaped literal ampersands."""
    if not text:
        return ""

    marker = "\0AMP\0"
    return text.replace("&&", marker).replace("&", "").replace(marker, "&")
