"""
Gesture action execution functions for the gesture system.
These functions handle executing different types of gestures:
- Brush preset selection
- Krita action execution
- Docker toggling
"""

from krita import Krita  # type: ignore
from ..utils.action_manager import ActionManager


def select_brush_preset_and_close(preset):
    """
    Select a brush preset in Krita.

    Args:
        preset: Krita brush preset object
    """
    try:
        app = Krita.instance()
        if app.activeWindow() and app.activeWindow().activeView():
            app.activeWindow().activeView().setCurrentBrushPreset(preset)
            print(f" Selected brush preset: {preset.name()}")
        else:
            print("L No active window/view found")
    except Exception as e:
        print(f"L Error selecting brush preset: {e}")


def select_brush_by_name(brush_name):
    """
    Select a brush preset by name.

    Args:
        brush_name: Name of the brush preset to select

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        app = Krita.instance()
        preset_dict = app.resources("preset")

        if brush_name in preset_dict:
            preset = preset_dict[brush_name]
            select_brush_preset_and_close(preset)
            return True
        else:
            print(f"L Brush preset '{brush_name}' not found")
            return False
    except Exception as e:
        print(f"L Error selecting brush by name: {e}")
        return False


def execute_action_by_name_and_close(action_name):
    """
    Execute a Krita action by name.

    Args:
        action_name: Internal ID/name of the Krita action to execute

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        print(f"Attempting to execute action: '{action_name}'")

        # Use the ActionManager that works in shortcut_manager.py
        if ActionManager.run_action(action_name):
            print(f" Successfully executed action via ActionManager: {action_name}")
            return True
        else:
            print(f"L ActionManager could not execute action: '{action_name}'")

            # Fallback: Try the old method
            app = Krita.instance()
            if app.activeWindow():
                window = app.activeWindow()
                action = window.action(action_name)
                if action:
                    action.trigger()
                    print(f" Successfully executed action via window.action: {action_name}")
                    return True
                else:
                    print(f"L Action '{action_name}' not found in Krita's action collection")
                    return False
            else:
                print("L No active window found")
                return False

    except Exception as e:
        print(f"L Error executing action {action_name}: {e}")
        import traceback
        traceback.print_exc()
        return False


def toggle_docker_by_keywords(keywords, description=None):
    """
    Toggle visibility of a Krita docker based on keywords.
    Generic function to toggle any docker based on keywords in the docker title.

    Args:
        keywords: List of keywords to match in the docker title (all must match)
        description: Optional description for logging purposes

    Returns:
        bool: True if docker was found and toggled, False otherwise
    """
    if description is None:
        description = f"Docker with keywords: {keywords}"

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
                    return True

        print(f"Could not find {description}")
        return False

    except Exception as e:
        print(f"Error toggling {description}: {e}")
        return False


def toggle_docker_by_name(docker_name):
    """
    Toggle visibility of a Krita docker by exact name match.

    Args:
        docker_name: Name (keyword) to match in the docker title

    Returns:
        bool: True if docker was found and toggled, False otherwise
    """
    return toggle_docker_by_keywords([docker_name], f"Docker: {docker_name}")


def execute_gesture(gesture_config):
    """
    Execute a gesture based on its configuration.

    Args:
        gesture_config: Dictionary containing gesture_type and parameters
            Example: {
                "gesture_type": "brush",
                "parameters": {"brush_name": "Paint Test 2"}
            }

    Returns:
        bool: True if successful, False otherwise
    """
    if not gesture_config:
        print("L No gesture configuration provided")
        return False

    gesture_type = gesture_config.get('gesture_type')
    parameters = gesture_config.get('parameters', {})

    if gesture_type == 'brush':
        brush_name = parameters.get('brush_name')
        if brush_name:
            return select_brush_by_name(brush_name)
        else:
            print("L No brush name in parameters")
            return False

    elif gesture_type == 'action':
        action_id = parameters.get('action_id')
        if action_id:
            return execute_action_by_name_and_close(action_id)
        else:
            print("L No action_id in parameters")
            return False

    elif gesture_type == 'docker_toggle':
        docker_name = parameters.get('docker_name')
        if docker_name:
            return toggle_docker_by_name(docker_name)
        else:
            print("L No docker_name in parameters")
            return False

    else:
        print(f"L Unknown gesture type: {gesture_type}")
        return False
