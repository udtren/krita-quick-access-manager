from krita import Krita  # type: ignore


class ActionManager:
    """Manages Krita actions discovery and execution"""

    @staticmethod
    def get_all_actions():
        """Get all available Krita actions"""
        all_actions = {}
        app = Krita.instance()
        main_window = app.activeWindow()

        if not main_window:
            return []

        qwin = main_window.qwindow()
        widgets = [qwin]

        # Add menu bar and toolbar if available
        if hasattr(qwin, "menuBar"):
            widgets.append(qwin.menuBar())
        if hasattr(qwin, "toolBar"):
            widgets.append(qwin.toolBar())

        # Recursively search for actions in widgets
        while widgets:
            widget = widgets.pop()
            if hasattr(widget, "actions"):
                actions = widget.actions
                if callable(actions):
                    actions = actions()

                for action in actions:
                    if action and hasattr(action, "objectName") and action.objectName():
                        all_actions[action.objectName()] = action

            # Add child widgets to search
            if hasattr(widget, "children"):
                widgets.extend(
                    child for child in widget.children() if hasattr(child, "actions")
                )

        # Add application-level actions
        for action in app.actions():
            if action and hasattr(action, "objectName") and action.objectName():
                all_actions[action.objectName()] = action

        return list(all_actions.values())

    @staticmethod
    def get_actions_dict():
        """Get all actions as a dictionary with objectName as key"""
        return {
            action.objectName(): action for action in ActionManager.get_all_actions()
        }

    @staticmethod
    def run_action(action_id):
        """Execute a Krita action by ID"""
        action = Krita.instance().action(action_id)
        if action:
            action.trigger()
            return True
        return False

    @staticmethod
    def get_action_by_id(action_id):
        """Get action by its object name"""
        return Krita.instance().action(action_id)
