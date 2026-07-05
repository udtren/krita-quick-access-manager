"""
Toggle buttons for pressure-sensitivity brush properties, embedded as the
bottom section of the color selector popup's right panel.

Reads/writes the current brush preset's XML directly (same technique as the
CompactBrushToggler plugin): pull the preset XML via Preset.toXML(), flip the
relevant <param> element's text between "true"/"false", write it back via
preset.fromXML(). PressureSize and PressureRotation each pair with a
"UseCurve" sub-param that must be kept in sync alongside the primary one.
"""

import re
import xml.etree.ElementTree as ET

from krita import Krita, Preset

from ...compat import QWidget, QGridLayout, QPushButton

# (display label, xml param name, paired sub-param name or "")
PROPERTIES = [
    ("Size", "PressureSize", "SizeUseCurve"),
    ("Opacity", "OpacityUseCurve", ""),
    ("Flow", "FlowUseCurve", ""),
    ("Rotation", "PressureRotation", "RotationUseCurve"),
]

_PATTERN_MD5_RE = re.compile(
    r'<param (?:type="string" )?name="Texture/Pattern/PatternMD5"'
    r'(?: type="string")?><!\[CDATA\[(.+?)\]\]></param>'
)


class BrushToggleWidget(QWidget):
    """Checkable buttons toggling PressureSize/OpacityUseCurve/FlowUseCurve/
    PressureRotation on the active brush preset."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.buttons = {}
        grid = QGridLayout()
        grid.setSpacing(4)
        grid.setContentsMargins(0, 0, 0, 0)

        for i, (label, name, sub_name) in enumerate(PROPERTIES):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setStyleSheet(
                "QPushButton { font-weight: bold; }"
                "QPushButton:checked { background-color: #2ecc71; }"
            )
            btn.toggled.connect(
                lambda checked, n=name, s=sub_name: self._on_toggled(n, s, checked)
            )
            grid.addWidget(btn, i // 2, i % 2)
            self.buttons[name] = btn

        self.setLayout(grid)
        self.refresh_from_current_brush()

    def _active_preset(self):
        app = Krita.instance()
        window = app.activeWindow()
        view = window.activeView() if window else None
        if not view:
            return None
        return Preset(view.currentBrushPreset())

    def _preset_xml(self, preset):
        xml_string = preset.toXML()
        match = _PATTERN_MD5_RE.search(xml_string)
        if match and re.search("[^a-zA-Z0-9+/=]", match.group(1)):
            xml_string = _PATTERN_MD5_RE.sub("", xml_string)
        return xml_string

    def refresh_from_current_brush(self):
        """Read the active brush preset and update each button's checked/
        enabled state to match. Called on construction and whenever the
        popup is shown, so switching brushes doesn't leave stale states."""
        preset = self._active_preset()
        if preset is None:
            return

        tree = ET.fromstring(self._preset_xml(preset))
        params = {param.get("name"): param for param in tree.findall("param")}

        for _, name, _sub_name in PROPERTIES:
            btn = self.buttons[name]
            param = params.get(name)
            btn.blockSignals(True)
            if param is not None:
                btn.setEnabled(True)
                btn.setChecked(param.text == "true")
            else:
                btn.setEnabled(False)
                btn.setChecked(False)
            btn.blockSignals(False)

    def _on_toggled(self, name, sub_name, checked):
        preset = self._active_preset()
        if preset is None:
            return

        tree = ET.fromstring(self._preset_xml(preset))
        new_value = "true" if checked else "false"
        for param in tree.findall("param"):
            param_name = param.get("name")
            if param_name == name or (sub_name and param_name == sub_name):
                param.text = new_value

        preset.fromXML(ET.tostring(tree, encoding="unicode"))
