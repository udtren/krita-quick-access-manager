from ..compat import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTabWidget,
)
from .tabs import MainTab, QuickAdjustTab, PopupTab, PresetManagerTab

# Tab index constants
TAB_MAIN = 0
TAB_QUICK_ADJUST = 1
TAB_POPUP = 2
TAB_PRESET_MANAGER = 3


class CommonConfigDialog(QDialog):
    """Settings dialog with tabs for each config category."""

    def __init__(self, config_path, parent=None, initial_tab=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(600, 500)

        self.main_tab = MainTab(config_path)
        self.quick_adjust_tab = QuickAdjustTab(config_path)
        self.popup_tab = PopupTab()
        self.preset_manager_tab = PresetManagerTab()

        self._setup_ui(initial_tab)
        self._setup_connections()

    def _setup_ui(self, initial_tab):
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self.main_tab.create_page(), "Main")
        self.tab_widget.addTab(self.quick_adjust_tab.create_page(), "Quick Adjust")
        self.tab_widget.addTab(self.popup_tab.create_page(), "Popup")
        self.tab_widget.addTab(self.preset_manager_tab.create_page(), "Preset Switcher")
        layout.addWidget(self.tab_widget)

        if initial_tab is not None:
            self.tab_widget.setCurrentIndex(initial_tab)

        layout.addWidget(QLabel("Some changes require Krita restart to take effect"))

        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.cancel_btn = QPushButton("Cancel")
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

    def _setup_connections(self):
        self.save_btn.clicked.connect(self._save_and_close)
        self.cancel_btn.clicked.connect(self.reject)

    def _save_and_close(self):
        self.main_tab.save()
        self.quick_adjust_tab.save()
        self.popup_tab.save()
        # preset_manager_tab saves immediately on delete — no save() needed
        self.accept()
