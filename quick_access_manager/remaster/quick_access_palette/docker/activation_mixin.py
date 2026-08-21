"""Click-time execution: run the action/brush/color/script/blend-mode/etc.
a placed item represents."""

import os

from krita import Krita, ManagedColor  # type: ignore

from ...compat import QColor, QMessageBox
from ...infrastructure import ActionManager, DockerManager


class ActivationMixin:
    """Requires `self.active_view()` (defined here) to be reachable, plus
    `self._action_map` initialized by the composed docker widget's
    `__init__`."""

    def action_map(self, refresh=False):
        """Krita's {objectName: QAction} table, discovered on first use.

        Deliberately not named `actions` - that would shadow QWidget.actions().
        """
        if refresh or self._action_map is None:
            self._action_map = ActionManager.get_actions_dict()
        return self._action_map

    def activate_brush(self, brush_name):
        if not brush_name:
            return
        preset = Krita.instance().resources("preset").get(brush_name)
        view = self.active_view()
        if preset and view:
            view.setCurrentBrushPreset(preset)

    def trigger_action(self, action_id):
        action = self.action_map().get(action_id)
        if action:
            action.trigger()

    def activate_docker_toggle(self, docker_id):
        if DockerManager:
            DockerManager.toggle_docker(docker_id)

    def activate_color(self, color):
        view = self.active_view()
        if not view:
            return
        managed_color = ManagedColor("RGBA", "U8", "")
        qcolor = QColor(color)
        managed_color.setComponents(
            [qcolor.blueF(), qcolor.greenF(), qcolor.redF(), 1.0]
        )
        view.setForeGroundColor(managed_color)

    def activate_brush_size(self, size_text):
        view = self.active_view()
        if not view or not size_text:
            return
        try:
            size = float(size_text)
        except ValueError:
            return
        view.setBrushSize(size)

    def activate_brush_blend_mode(self, blend_mode):
        view = self.active_view()
        if not view or not blend_mode:
            return
        try:
            view.setCurrentBlendingMode(blend_mode)
        except Exception:
            pass

    def run_script(self, script_path):
        if not script_path or not os.path.isfile(script_path):
            QMessageBox.warning(
                self,
                "Script Not Found",
                f"The script file could not be found:\n{script_path}",
            )
            return
        try:
            with open(script_path, "r", encoding="utf-8") as script_file:
                source = script_file.read()
            exec(
                compile(source, script_path, "exec"),
                {"__name__": "__main__", "Krita": Krita},
            )
        except Exception as exc:
            QMessageBox.warning(self, "Script Error", f"Failed to run script:\n{exc}")

    def active_view(self):
        window = Krita.instance().activeWindow()
        if window:
            return window.activeView()
        return None
