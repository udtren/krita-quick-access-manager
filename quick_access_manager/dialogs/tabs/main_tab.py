import json
from ...compat import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QScrollArea, Qt,
    QCheckBox, QGroupBox,
)


class MainTab:
    """Tab for main color/font/layout config (common.json)."""

    def __init__(self, config_path):
        self.config_path = config_path
        self.fields = {}
        self.config = {}
        self._layout = None

    def create_page(self):
        page = QWidget()
        outer = QVBoxLayout()
        page.setLayout(outer)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        inner = QWidget()
        self._layout = QVBoxLayout()
        inner.setLayout(self._layout)
        scroll.setWidget(inner)
        outer.addWidget(scroll)

        self._load()
        return page

    def _load(self):
        with open(self.config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)

        layout = self._layout
        for section in ["color", "font", "layout"]:
            group = self.config.get(section, {})
            layout.addWidget(QLabel(f"[{section}]"))
            for key, value in group.items():
                hl = QHBoxLayout()
                label = QLabel(key)
                label.setAlignment(Qt.AlignLeft)
                edit = QLineEdit(str(value))
                edit.setFixedWidth(80)
                edit.setAlignment(Qt.AlignRight)
                hl.addWidget(label)
                hl.addStretch()
                hl.addWidget(edit)
                layout.addLayout(hl)
                self.fields[(section, key)] = edit

        perf_group = QGroupBox("Performance")
        perf_layout = QVBoxLayout()
        perf_group.setLayout(perf_layout)
        perf_config = self.config.get("performance", {})
        self._perf_mode_cb = QCheckBox("Enable Performance Mode")
        self._perf_mode_cb.setChecked(bool(perf_config.get("enable_performance_mode", False)))
        self._perf_mode_cb.setToolTip(
            "Disables the brush adjust docker, gesture system, and color selector docker.\n"
            "Restart Krita after changing this setting."
        )
        perf_layout.addWidget(self._perf_mode_cb)
        layout.addWidget(perf_group)

        layout.addStretch()

    def save(self):
        for (section, key), edit in self.fields.items():
            val = edit.text()
            if section == "layout":
                try:
                    val = int(val)
                except Exception:
                    pass
            self.config[section][key] = val
        self.config.setdefault("performance", {})["enable_performance_mode"] = self._perf_mode_cb.isChecked()
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=4)
