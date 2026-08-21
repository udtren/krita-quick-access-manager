"""Krita action discovery helpers for the remastered palette."""

from krita import Krita  # type: ignore


class ActionManager:
    """Discover and run Krita actions without depending on legacy modules."""

    @staticmethod
    def get_all_actions():
        all_actions = {}
        app = Krita.instance()
        main_window = app.activeWindow()

        if main_window:
            qwin = main_window.qwindow()
            widgets = [qwin]

            if hasattr(qwin, "menuBar"):
                widgets.append(qwin.menuBar())
            if hasattr(qwin, "toolBar"):
                widgets.append(qwin.toolBar())

            while widgets:
                widget = widgets.pop()
                if hasattr(widget, "actions"):
                    actions = widget.actions
                    if callable(actions):
                        actions = actions()

                    for action in actions:
                        if action and hasattr(action, "objectName") and action.objectName():
                            all_actions[action.objectName()] = action

                if hasattr(widget, "children"):
                    widgets.extend(
                        child for child in widget.children() if hasattr(child, "actions")
                    )

        for action in app.actions():
            if action and hasattr(action, "objectName") and action.objectName():
                all_actions[action.objectName()] = action

        return list(all_actions.values())

    @staticmethod
    def get_actions_dict():
        return {action.objectName(): action for action in ActionManager.get_all_actions()}

    @staticmethod
    def get_action_by_id(action_id):
        action = Krita.instance().action(action_id)
        if action:
            return action
        return ActionManager.get_actions_dict().get(action_id)

    @staticmethod
    def run_action(action_id):
        action = ActionManager.get_action_by_id(action_id)
        if action:
            action.trigger()
            return True
        return False
