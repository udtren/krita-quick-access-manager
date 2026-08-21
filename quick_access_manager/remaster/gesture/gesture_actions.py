"""
Gesture action execution functions for the gesture system.
These functions handle executing different types of gestures:
- Brush preset selection
- Krita action execution
- Docker toggling
"""

from krita import Krita  # type: ignore

from ..infrastructure import ActionManager


def select_brush_preset_and_close(preset):
    try:
        app = Krita.instance()
        if app.activeWindow() and app.activeWindow().activeView():
            app.activeWindow().activeView().setCurrentBrushPreset(preset)
        else:
            print("Quick Access Palette gesture: no active window/view found")
    except Exception as e:
        print(f"Quick Access Palette gesture: error selecting brush preset: {e}")


def select_brush_by_name(brush_name):
    try:
        app = Krita.instance()
        preset_dict = app.resources("preset")

        if brush_name in preset_dict:
            preset = preset_dict[brush_name]
            select_brush_preset_and_close(preset)
            return True
        print(f"Quick Access Palette gesture: brush preset '{brush_name}' not found")
        return False
    except Exception as e:
        print(f"Quick Access Palette gesture: error selecting brush by name: {e}")
        return False


def execute_action_by_name_and_close(action_name):
    try:
        if ActionManager.run_action(action_name):
            return True

        app = Krita.instance()
        if app.activeWindow():
            action = app.activeWindow().action(action_name)
            if action:
                action.trigger()
                return True
            return False
        print("Quick Access Palette gesture: no active window found")
        return False
    except Exception:
        import traceback

        traceback.print_exc()
        return False


def toggle_docker_by_keywords(keywords, description=None):
    if description is None:
        description = f"Docker with keywords: {keywords}"

    app = Krita.instance()
    try:
        window = app.activeWindow()
        if window:
            for docker in window.dockers():
                docker_title = docker.windowTitle().lower()
                if all(keyword.lower() in docker_title for keyword in keywords):
                    if docker.isVisible():
                        docker.hide()
                    else:
                        docker.show()
                        docker.raise_()
                    return True
        return False
    except Exception:
        return False


def toggle_docker_by_name(docker_name):
    return toggle_docker_by_keywords([docker_name], f"Docker: {docker_name}")


def execute_gesture(gesture_config):
    """Execute a gesture based on its configuration.

    Example: {"gesture_type": "brush", "parameters": {"brush_name": "..."}}
    """
    if not gesture_config:
        return False

    gesture_type = gesture_config.get("gesture_type")
    parameters = gesture_config.get("parameters", {})

    if gesture_type == "brush":
        brush_name = parameters.get("brush_name")
        return select_brush_by_name(brush_name) if brush_name else False

    if gesture_type == "action":
        action_id = parameters.get("action_id")
        return execute_action_by_name_and_close(action_id) if action_id else False

    if gesture_type == "docker_toggle":
        docker_name = parameters.get("docker_name")
        return toggle_docker_by_name(docker_name) if docker_name else False

    return False
