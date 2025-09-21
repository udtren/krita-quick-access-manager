
import json
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QPushButton)

class CommonConfigDialog(QDialog):
    """Dialog for editing common configuration settings"""
    
    def __init__(self, config_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.config_path = config_path
        self.resize(400, 300)
        
        self.setup_ui()
        self.load_config()
        self.setup_connections()
    
    def setup_ui(self):
        """Setup the UI elements"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        self.fields = {}
        
        # Button layout
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.cancel_btn = QPushButton("Cancel")
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)
    
    def load_config(self):
        """Load configuration from file"""
        with open(self.config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)
        
        # Create editable fields for color/font/layout
        layout = self.layout()
        
        for section in ["color", "font", "layout"]:
            group = self.config.get(section, {})
            layout.insertWidget(layout.count() - 1, QLabel(f"[{section}]"))
            
            for key, value in group.items():
                hlayout = QHBoxLayout()
                label = QLabel(key)
                edit = QLineEdit(str(value))
                hlayout.addWidget(label)
                hlayout.addWidget(edit)
                layout.insertLayout(layout.count() - 1, hlayout)
                self.fields[(section, key)] = edit
    
    def setup_connections(self):
        """Setup button connections"""
        self.save_btn.clicked.connect(self.save_and_close)
        self.cancel_btn.clicked.connect(self.reject)
    
    def save_and_close(self):
        """Save configuration and close dialog"""
        # Save edits to config
        for (section, key), edit in self.fields.items():
            val = edit.text()
            
            # Type conversion for layout section
            if section == "layout":
                try:
                    val = int(val)
                except Exception:
                    pass
            
            self.config[section][key] = val
        
        # Write to file
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=4)
        
        self.accept()