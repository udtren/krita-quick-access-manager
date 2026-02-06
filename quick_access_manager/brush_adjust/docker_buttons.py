"""
Docker button management for toggling Krita dockers.
"""

import json
import os
from PyQt6.QtWidgets import QPushButton
from PyQt6.QtGui import QIcon
from krita import Krita  # type: ignore

from ..config.quick_adjust_docker_loader import get_font_size


def load_docker_buttons_config():
    """Load docker buttons configuration from JSON file"""
    try:
        # Get the directory where the parent package is located
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_dir = os.path.join(current_dir, "config")
        config_file = os.path.join(config_dir, "docker_buttons.json")

        if os.path.exists(config_file):
            with open(config_file, "r") as f:
                config = json.load(f)
                print(
                    f"Loaded docker buttons config: {len(config.get('docker_buttons', []))} buttons"
                )
                return config
        else:
            print(f"Docker buttons config file not found: {config_file}")
            print("Creating default config file...")

            # Create the config directory if it doesn't exist
            os.makedirs(config_dir, exist_ok=True)

            # Get default configuration
            default_config = get_default_docker_config()

            # Write default config to file
            with open(config_file, "w") as f:
                json.dump(default_config, f, indent=4)

            print(f"Created default docker buttons config file: {config_file}")
            return default_config

    except Exception as e:
        print(f"Error loading docker buttons config: {e}")
        return get_default_docker_config()


def get_default_docker_config():
    """Return default docker configuration if JSON file is not available"""
    return {
        "docker_buttons": [
            {
                "button_name": "Tool",
                "button_width": 40,
                "button_icon": "",
                "docker_keywords": ["tool", "option"],
                "description": "Tool Options Docker",
            },
            {
                "button_name": "Layers",
                "button_width": 50,
                "button_icon": "",
                "docker_keywords": ["layer"],
                "description": "Layers Docker",
            },
            {
                "button_name": "Brush",
                "button_width": 50,
                "button_icon": "",
                "docker_keywords": ["brush", "preset"],
                "description": "Brush Presets Docker",
            },
        ]
    }


def create_docker_buttons(layout, docker_buttons_config, toggle_callback):
    """
    Dynamically create docker toggle buttons based on configuration.

    Args:
        layout: Qt layout to add buttons to
        docker_buttons_config: Configuration dict with docker button settings
        toggle_callback: Callback function for toggle (receives keywords, description)
    """
    docker_buttons = docker_buttons_config.get("docker_buttons", [])
    if not docker_buttons:
        return

    print(f"Creating {len(docker_buttons)} docker buttons")

    for button_config in docker_buttons:
        button_icon = button_config.get("button_icon", "")

        # Check if button_icon is empty
        if not button_icon:
            # Create button with text
            button = QPushButton(button_config["button_name"])
            button.setStyleSheet(f"font-size: {get_font_size()}; padding: 2px 8px;")
            button.setFixedWidth(button_config["button_width"])
        else:
            # Create button with icon
            button = QPushButton()
            icon_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "config",
                "icon",
                button_icon,
            )

            if os.path.exists(icon_path):
                icon = QIcon(icon_path)
                button.setIcon(icon)
                button.setFixedSize(18, 18)
            else:
                # Fallback to text if icon not found
                print(f"Icon not found: {icon_path}, using text instead")
                button.setText(button_config["button_name"])
                button.setStyleSheet(f"font-size: {get_font_size()}; padding: 2px 8px;")
                button.setFixedWidth(button_config["button_width"])

        button.setToolTip(button_config["description"])

        # Create a closure to capture the button configuration
        def make_docker_toggle_handler(config):
            def toggle_docker():
                toggle_callback(config["docker_keywords"], config["description"])

            return toggle_docker

        button.clicked.connect(make_docker_toggle_handler(button_config))
        layout.addWidget(button)


def toggle_docker_by_keywords(keywords, description):
    """
    Generic function to toggle any docker based on keywords.

    Args:
        keywords: List of keywords to match in docker title
        description: Description for logging purposes
    """
    print(f"Toggling {description}")

    app = Krita.instance()
    try:
        window = app.activeWindow()
        if window:
            dockers = window.dockers()
            for docker in dockers:
                docker_title = docker.windowTitle().lower()

                # Check if all keywords are present in the docker title
                if all(keyword.lower() in docker_title for keyword in keywords):
                    if docker.isVisible():
                        docker.hide()
                        print(f"Hid {description}: {docker.windowTitle()}")
                    else:
                        docker.show()
                        docker.raise_()
                        print(f"Showed {description}: {docker.windowTitle()}")
                    return

        print(f"Could not find {description}")

    except Exception as e:
        print(f"Error toggling {description}: {e}")
