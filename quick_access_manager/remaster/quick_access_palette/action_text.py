"""Helpers for displaying Krita action text outside native Qt menus."""


def display_action_text(text: str) -> str:
    """Return QAction text without Qt mnemonic markers.

    Qt uses a single ampersand to mark menu mnemonics (for example
    "Add &Filter Layer..."). A doubled ampersand is an escaped literal "&",
    so preserve that while removing mnemonic markers for table/combo display.
    """
    placeholder = "\0"
    return text.replace("&&", placeholder).replace("&", "").replace(placeholder, "&")
