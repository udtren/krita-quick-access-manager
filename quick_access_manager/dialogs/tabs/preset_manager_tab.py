import json
import os
from ...compat import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QScrollArea, QCheckBox, QComboBox,
)
from ...utils.config_utils import get_presets_config_dir


class PresetManagerTab:
    """Tab for viewing and deleting saved brush preset XML configs."""

    def __init__(self):
        self._checkboxes = {}
        self._current_data = {}
        self._combo = None
        self._list_layout = None

    def create_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        page.setLayout(layout)

        layout.addWidget(QLabel("[Brush Preset Configs]"))
        layout.addWidget(
            QLabel("Select a brush file to view its saved configs. Check entries and click Delete Selected to remove them.")
        )

        self._combo = QComboBox()
        self._combo.currentIndexChanged.connect(self._on_file_selected)
        layout.addWidget(self._combo)

        list_widget = QWidget()
        self._list_layout = QVBoxLayout()
        self._list_layout.setContentsMargins(4, 4, 4, 4)
        self._list_layout.setSpacing(2)
        list_widget.setLayout(self._list_layout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(list_widget)
        scroll.setMinimumHeight(200)
        layout.addWidget(scroll)

        btn_layout = QHBoxLayout()
        delete_btn = QPushButton("Delete Selected")
        delete_btn.clicked.connect(self._delete_selected)
        btn_layout.addWidget(delete_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        layout.addStretch()

        self._populate_combo()
        return page

    def _populate_combo(self):
        presets_dir = get_presets_config_dir()
        saved_index = self._combo.currentIndex()

        self._combo.blockSignals(True)
        self._combo.clear()
        if os.path.isdir(presets_dir):
            for fname in sorted(os.listdir(presets_dir)):
                if fname.endswith(".json"):
                    self._combo.addItem(fname[:-5], fname)
        self._combo.blockSignals(False)

        if self._combo.count() > 0:
            new_index = max(0, min(saved_index, self._combo.count() - 1))
            self._combo.setCurrentIndex(new_index)
            self._on_file_selected(new_index)

    def _on_file_selected(self, index):
        for i in reversed(range(self._list_layout.count())):
            item = self._list_layout.itemAt(i)
            if item and item.widget():
                item.widget().setParent(None)
        self._checkboxes.clear()
        self._current_data = {}

        fname = self._combo.itemData(index)
        if not fname:
            return

        filepath = os.path.join(get_presets_config_dir(), fname)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                self._current_data = json.load(f)
        except (json.JSONDecodeError, IOError):
            return

        for config_name in self._current_data:
            cb = QCheckBox(config_name)
            self._list_layout.addWidget(cb)
            self._checkboxes[config_name] = cb

    def _delete_selected(self):
        to_delete = [name for name, cb in self._checkboxes.items() if cb.isChecked()]
        if not to_delete:
            return

        fname = self._combo.currentData()
        if not fname:
            return

        filepath = os.path.join(get_presets_config_dir(), fname)
        for name in to_delete:
            self._current_data.pop(name, None)

        if self._current_data:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(self._current_data, f, indent=4, ensure_ascii=False)
        else:
            try:
                os.remove(filepath)
            except OSError:
                pass

        self._populate_combo()
