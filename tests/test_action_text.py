import unittest

from quick_access_manager.remaster.quick_access_palette.presentation import (
    display_action_text,
)


class ActionTextDisplayTest(unittest.TestCase):
    def test_removes_qt_mnemonic_ampersands(self):
        self.assertEqual(
            display_action_text("Add &Filter Layer..."), "Add Filter Layer..."
        )

    def test_preserves_escaped_literal_ampersands(self):
        self.assertEqual(display_action_text("Save && Close"), "Save & Close")


if __name__ == "__main__":
    unittest.main()
