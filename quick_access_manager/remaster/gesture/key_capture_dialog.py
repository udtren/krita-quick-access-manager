from ..compat import QDialog, QHBoxLayout, QKeyEvent, QLabel, QPushButton, Qt, QVBoxLayout


class KeyCaptureDialog(QDialog):
    """Dialog for capturing a key press for gesture trigger"""

    def __init__(self, config_name, parent=None):
        super().__init__(parent)
        self.config_name = config_name
        self.captured_key = None
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Configure Gesture Key")
        self.resize(400, 200)
        layout = QVBoxLayout()

        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #e0e0e0;
            }
            QLabel {
                color: #e0e0e0;
                background-color: transparent;
                font-size: 14px;
            }
            QPushButton {
                background-color: #3c3c3c;
                color: #e0e0e0;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
                border: 1px solid #666;
            }
            QPushButton:pressed {
                background-color: #2a2a2a;
                border: 1px solid #444;
            }
        """)

        title_label = QLabel(f"Configure gesture key for: {self.config_name}")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        instruction_label = QLabel("Press any key (A-Z, 0-9, F1-F12, etc.)")
        instruction_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(instruction_label)

        self.key_label = QLabel("No key captured")
        self.key_label.setAlignment(Qt.AlignCenter)
        self.key_label.setStyleSheet(
            "QLabel { font-size: 24px; font-weight: bold; color: #4FC3F7; padding: 20px; }"
        )
        layout.addWidget(self.key_label)

        layout.addStretch()

        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("OK")
        self.cancel_btn = QPushButton("Cancel")
        self.clear_btn = QPushButton("Clear Key")
        btn_layout.addWidget(self.clear_btn)
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        self.clear_btn.clicked.connect(self.clear_key)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key_Shift, Qt.Key_Control, Qt.Key_Alt, Qt.Key_Meta):
            return

        key_text = event.text().upper()
        key = event.key()
        if key == Qt.Key_Escape:
            self.reject()
            return
        if Qt.Key_F1 <= key <= Qt.Key_F12:
            key_text = f"F{key - Qt.Key_F1 + 1}"
        elif key == Qt.Key_Space:
            key_text = "SPACE"
        elif key in (Qt.Key_Return, Qt.Key_Enter):
            key_text = "ENTER"
        elif key == Qt.Key_QuoteLeft:
            key_text = "`"
        elif not key_text or not key_text.isalnum():
            return

        self.captured_key = key_text
        self.key_label.setText(f"Key: {key_text}")

    def clear_key(self):
        self.captured_key = None
        self.key_label.setText("No key captured")

    def get_captured_key(self):
        return self.captured_key
