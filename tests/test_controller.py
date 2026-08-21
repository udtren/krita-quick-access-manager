"""PaletteController tests - no krita, no Qt.

Every test gets its own temp directory so PaletteRepository/AliasRepository
never touch the real Krita config dir (see infrastructure/paths.py, which
derives that path from the plugin's on-disk install location).
"""

import json
import os
import tempfile
import unittest
from unittest import mock

from quick_access_manager.remaster.infrastructure import (
    AliasRepository,
    PaletteRepository,
)
from quick_access_manager.remaster.quick_access_palette.controller import (
    PaletteController,
)


class ControllerTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        base = self._tmp.name
        self.repository = PaletteRepository(
            path=os.path.join(base, "quick_access_palette.json"),
            settings_path=os.path.join(base, "settings.json"),
        )
        self.alias_repository = AliasRepository(
            path=os.path.join(base, "alias_config.json")
        )

    def make_controller(self):
        return PaletteController(
            repository=self.repository, alias_repository=self.alias_repository
        )


class AddItemPlacementTests(ControllerTestCase):
    def test_add_brush_defaults_to_the_row_below_the_last_item(self):
        controller = self.make_controller()
        controller.add_brush("Brush A")
        controller.add_brush("Brush B")
        grid = controller.active_grid()
        rows = sorted(item.row for item in grid.items)
        self.assertEqual(rows, [0, 1])

    def test_sequential_placement_fills_one_row_left_to_right(self):
        controller = self.make_controller()
        controller.set_columns(3)
        controller.begin_sequential_placement()
        for name in ("A", "B", "C", "D"):
            controller.add_brush(name)
        controller.end_sequential_placement()

        grid = controller.active_grid()
        positions = {
            item.payload["brush_name"]: (item.row, item.col) for item in grid.items
        }
        self.assertEqual(positions["A"], (0, 0))
        self.assertEqual(positions["B"], (0, 1))
        self.assertEqual(positions["C"], (0, 2))
        # Grid is 3 columns wide; the 4th item wraps to the next row.
        self.assertEqual(positions["D"], (1, 0))

    def test_sequential_placement_skips_a_wider_item_that_would_overflow(self):
        controller = self.make_controller()
        controller.set_columns(3)
        controller.begin_sequential_placement()
        controller.add_brush("A")
        controller.add_brush("B")
        # Two cells left in the row; an action item needs col_span >= 2, so
        # it fits, but the next item after it must wrap.
        controller.add_action("some.action")
        controller.add_brush("C")
        controller.end_sequential_placement()

        grid = controller.active_grid()
        by_name = {}
        for item in grid.items:
            key = item.payload.get("brush_name") or item.payload.get("action_id")
            by_name[key] = (item.row, item.col)
        self.assertEqual(by_name["A"], (0, 0))
        self.assertEqual(by_name["B"], (0, 1))
        self.assertEqual(by_name["some.action"], (1, 0))
        self.assertEqual(by_name["C"], (1, 2))

    def test_sequential_cursor_is_scoped_to_the_grid_it_was_opened_on(self):
        controller = self.make_controller()
        controller.begin_sequential_placement()
        # Switching the active grid mid-session (new tab) should make the
        # cursor inert rather than misplacing items into the wrong grid.
        controller.add_tab("Second Tab")
        controller.add_brush("A")
        grid = controller.active_grid()
        self.assertEqual((grid.items[0].row, grid.items[0].col), (0, 0))

    def test_ending_sequential_placement_restores_default_placement(self):
        controller = self.make_controller()
        controller.begin_sequential_placement()
        controller.add_brush("A")
        controller.end_sequential_placement()
        controller.add_brush("B")
        grid = controller.active_grid()
        positions = {
            item.payload["brush_name"]: (item.row, item.col) for item in grid.items
        }
        # Without an active sequential session, B goes below the last row.
        self.assertEqual(positions["B"], (1, 0))


class MoveResizeRemoveTests(ControllerTestCase):
    def test_move_item_relocates_it(self):
        controller = self.make_controller()
        controller.add_brush("A")
        item_id = controller.active_grid().items[0].id
        controller.move_item(item_id, row=2, col=3)
        moved = controller.active_grid().items[0]
        self.assertEqual((moved.row, moved.col), (2, 3))

    def test_remove_item_drops_it_from_the_grid(self):
        controller = self.make_controller()
        controller.add_brush("A")
        controller.add_brush("B")
        item_id = controller.active_grid().items[0].id
        controller.remove_item(item_id)
        remaining_ids = {item.id for item in controller.active_grid().items}
        self.assertNotIn(item_id, remaining_ids)
        self.assertEqual(len(remaining_ids), 1)

    def test_set_columns_persists_and_reflows_validation(self):
        controller = self.make_controller()
        controller.add_action("some.action")  # default col_span >= 2
        controller.set_columns(1)
        result = controller.validate_active_grid()
        self.assertFalse(result.valid)


class DockerToggleItemTests(ControllerTestCase):
    def test_add_docker_toggle_defaults_to_two_by_one_text_button(self):
        controller = self.make_controller()
        controller.add_docker_toggle("docker.id")
        item = controller.active_grid().items[0]
        self.assertEqual(item.type, "docker_toggle")
        self.assertEqual(item.payload.get("docker_id"), "docker.id")
        self.assertEqual(item.row_span, 1)
        self.assertGreaterEqual(item.col_span, 2)

    def test_docker_toggle_text_button_keeps_resized_width_on_reload(self):
        controller = self.make_controller()
        controller.add_docker_toggle("wide.docker")
        item_id = controller.active_grid().items[0].id
        controller.resize_item(item_id, col_span=4)

        reloaded = self.make_controller()
        self.assertEqual(reloaded.active_grid().items[0].col_span, 4)

    def test_docker_toggle_text_button_can_stay_one_by_one_after_property_update(self):
        controller = self.make_controller()
        controller.add_docker_toggle("docker.id")
        item_id = controller.active_grid().items[0].id
        controller.resize_item(item_id, col_span=1)
        controller.update_docker_toggle_item(item_id, "docker.id")

        item = controller.active_grid().items[0]
        self.assertEqual(item.col_span, 1)

    def test_alias_icon_forces_docker_toggle_col_span_to_one_on_load(self):
        controller = self.make_controller()
        controller.add_docker_toggle("iconified.docker")
        item_id = controller.active_grid().items[0].id
        controller.resize_item(item_id, col_span=4)
        self.alias_repository.save(
            {"actions": {}, "dockers": {"iconified.docker": {"icon_name": "foo.png"}}}
        )

        reloaded = self.make_controller()
        self.assertEqual(reloaded.active_grid().items[0].col_span, 1)


class ScriptItemTests(ControllerTestCase):
    def test_add_script_defaults_to_two_by_one_text_button(self):
        controller = self.make_controller()
        controller.add_script("script.py")
        item = controller.active_grid().items[0]
        self.assertEqual(item.type, "script")
        self.assertEqual(item.payload.get("script_path"), "script.py")
        self.assertEqual(item.row_span, 1)
        self.assertGreaterEqual(item.col_span, 2)

    def test_script_text_button_keeps_resized_width_on_reload(self):
        controller = self.make_controller()
        controller.add_script("script.py")
        item_id = controller.active_grid().items[0].id
        controller.resize_item(item_id, col_span=4)

        reloaded = self.make_controller()
        self.assertEqual(reloaded.active_grid().items[0].col_span, 4)

    def test_script_text_button_can_stay_one_by_one_after_property_update(self):
        controller = self.make_controller()
        controller.add_script("script.py")
        item_id = controller.active_grid().items[0].id
        controller.resize_item(item_id, col_span=1)
        controller.update_script_item(item_id, {"customName": "Run"})

        item = controller.active_grid().items[0]
        self.assertEqual(item.col_span, 1)

    def test_icon_script_is_one_by_one_on_add_and_reload(self):
        controller = self.make_controller()
        controller.add_script("script.py", config={"icon_name": "foo.png"})
        item = controller.active_grid().items[0]
        self.assertEqual(item.col_span, 1)

        reloaded = self.make_controller()
        self.assertEqual(reloaded.active_grid().items[0].col_span, 1)


class BrushSizeItemTests(ControllerTestCase):
    def test_add_brush_size_creates_a_one_by_one_item_with_text(self):
        controller = self.make_controller()
        controller.add_brush_size("25")
        item = controller.active_grid().items[0]
        self.assertEqual(item.type, "brush_size")
        self.assertEqual(item.payload.get("text"), "25")
        self.assertEqual((item.row_span, item.col_span), (1, 1))

    def test_add_brush_size_accepts_style_config(self):
        controller = self.make_controller()
        controller.add_brush_size(
            "10",
            config={
                "fontSize": "20",
                "backgroundColor": "#111111",
                "fontColor": "#eeeeee",
            },
        )
        item = controller.active_grid().items[0]
        self.assertEqual(item.payload["fontSize"], "20")
        self.assertEqual(item.payload["backgroundColor"], "#111111")
        self.assertEqual(item.payload["fontColor"], "#eeeeee")

    def test_update_brush_size_item_replaces_payload_fields(self):
        controller = self.make_controller()
        controller.add_brush_size("10")
        item_id = controller.active_grid().items[0].id
        controller.update_brush_size_item(item_id, {"text": "50", "fontSize": "24"})
        item = controller.active_grid().items[0]
        self.assertEqual(item.payload["text"], "50")
        self.assertEqual(item.payload["fontSize"], "24")

    def test_update_brush_size_item_rejects_wrong_item_type(self):
        controller = self.make_controller()
        controller.add_brush("A")
        item_id = controller.active_grid().items[0].id
        with self.assertRaises(ValueError):
            controller.update_brush_size_item(item_id, {"text": "50"})

    def test_brush_size_survives_reload_from_disk(self):
        controller = self.make_controller()
        controller.add_brush_size("42", config={"fontColor": "#abcdef"})
        reloaded = self.make_controller()
        item = reloaded.active_grid().items[0]
        self.assertEqual(item.payload["text"], "42")
        self.assertEqual(item.payload["fontColor"], "#abcdef")


class BrushBlendModeItemTests(ControllerTestCase):
    def test_add_brush_blend_mode_creates_a_two_by_one_item_with_text(self):
        controller = self.make_controller()
        controller.add_brush_blend_mode("multiply")
        item = controller.active_grid().items[0]
        self.assertEqual(item.type, "brush_blend_mode")
        self.assertEqual(item.payload.get("text"), "multiply")
        self.assertEqual((item.row_span, item.col_span), (1, 2))

    def test_add_brush_blend_mode_accepts_style_config(self):
        controller = self.make_controller()
        controller.add_brush_blend_mode(
            "screen",
            config={
                "fontSize": "16",
                "backgroundColor": "#111111",
                "fontColor": "#eeeeee",
            },
        )
        item = controller.active_grid().items[0]
        self.assertEqual(item.payload["fontSize"], "16")
        self.assertEqual(item.payload["backgroundColor"], "#111111")
        self.assertEqual(item.payload["fontColor"], "#eeeeee")

    def test_update_brush_blend_mode_item_replaces_payload_fields(self):
        controller = self.make_controller()
        controller.add_brush_blend_mode("multiply")
        item_id = controller.active_grid().items[0].id
        controller.update_brush_blend_mode_item(
            item_id, {"text": "darken", "fontSize": "20"}
        )
        item = controller.active_grid().items[0]
        self.assertEqual(item.payload["text"], "darken")
        self.assertEqual(item.payload["fontSize"], "20")

    def test_update_brush_blend_mode_item_rejects_wrong_item_type(self):
        controller = self.make_controller()
        controller.add_brush("A")
        item_id = controller.active_grid().items[0].id
        with self.assertRaises(ValueError):
            controller.update_brush_blend_mode_item(item_id, {"text": "multiply"})

    def test_brush_blend_mode_survives_reload_from_disk(self):
        controller = self.make_controller()
        controller.add_brush_blend_mode("multiply", config={"fontColor": "#abcdef"})
        reloaded = self.make_controller()
        item = reloaded.active_grid().items[0]
        self.assertEqual(item.payload["text"], "multiply")
        self.assertEqual(item.payload["fontColor"], "#abcdef")

    def test_add_brush_blend_mode_default_position_respects_its_own_width(self):
        # The 2-wide item must not collide with an existing item in the row
        # it's placed below.
        controller = self.make_controller()
        controller.set_columns(4)
        controller.add_brush("A")
        controller.add_brush_blend_mode("multiply")
        grid = controller.active_grid()
        self.assertTrue(controller.validate_active_grid().valid)
        self.assertEqual(len(grid.items), 2)


class SeparatorOrientationTests(ControllerTestCase):
    def test_add_separator_defaults_to_horizontal(self):
        controller = self.make_controller()
        controller.add_separator()
        item = controller.active_grid().items[0]
        self.assertEqual(item.payload.get("orientation"), "horizontal")
        self.assertEqual(item.row_span, 1)

    def test_add_separator_vertical_spans_multiple_rows_and_one_column(self):
        controller = self.make_controller()
        controller.add_separator(orientation="vertical")
        item = controller.active_grid().items[0]
        self.assertEqual(item.payload.get("orientation"), "vertical")
        self.assertEqual(item.col_span, 1)
        self.assertGreater(item.row_span, 1)

    def test_sequential_placement_advances_past_a_vertical_separators_single_column(self):
        # A vertical separator only claims one column, so the cursor should
        # move one cell right (same as any col_span=1 item), not skip the
        # rows it occupies below.
        controller = self.make_controller()
        controller.set_columns(3)
        controller.begin_sequential_placement()
        controller.add_separator(orientation="vertical")
        controller.add_brush("A")
        controller.end_sequential_placement()

        grid = controller.active_grid()
        by_kind = {
            (item.payload.get("orientation") or item.payload.get("brush_name")): item
            for item in grid.items
        }
        self.assertEqual((by_kind["vertical"].row, by_kind["vertical"].col), (0, 0))
        self.assertEqual((by_kind["A"].row, by_kind["A"].col), (0, 1))


class TabBarStyleSettingsTests(ControllerTestCase):
    def test_defaults_are_populated_without_any_saved_settings(self):
        controller = self.make_controller()
        style = controller.tab_bar_settings()
        self.assertEqual(
            set(style),
            {
                "active_font_size",
                "active_font_color",
                "active_background_color",
                "inactive_font_size",
                "inactive_font_color",
                "inactive_background_color",
            },
        )
        self.assertIsInstance(style["active_font_size"], int)

    def test_floating_widget_visibility_defaults_to_off(self):
        controller = self.make_controller()
        quick_adjust = controller.quick_adjust_settings()
        self.assertFalse(quick_adjust["tool_options_start_visible"])
        self.assertFalse(quick_adjust["rotation_widget_start_visible"])

    def test_update_settings_persists_tab_style_and_survives_reload(self):
        controller = self.make_controller()
        controller.update_settings(
            tab_active_font_size=16,
            tab_active_font_color="#111111",
            tab_active_background_color="#222222",
            tab_inactive_font_size=9,
            tab_inactive_font_color="#333333",
            tab_inactive_background_color="#444444",
        )
        reloaded = self.make_controller()
        style = reloaded.tab_bar_settings()
        self.assertEqual(style["active_font_size"], 16)
        self.assertEqual(style["active_font_color"], "#111111")
        self.assertEqual(style["active_background_color"], "#222222")
        self.assertEqual(style["inactive_font_size"], 9)
        self.assertEqual(style["inactive_font_color"], "#333333")
        self.assertEqual(style["inactive_background_color"], "#444444")

    def test_update_settings_leaves_tab_style_untouched_when_omitted(self):
        controller = self.make_controller()
        controller.update_settings(tab_active_font_color="#111111")
        controller.update_settings(docker_icon_size=48)  # unrelated update
        style = controller.tab_bar_settings()
        self.assertEqual(style["active_font_color"], "#111111")


class TabManagementTests(ControllerTestCase):
    def test_add_tab_becomes_active(self):
        controller = self.make_controller()
        original_id = controller.active_tab_id
        tab = controller.add_tab("New Tab")
        self.assertEqual(controller.active_tab_id, tab.id)
        self.assertNotEqual(controller.active_tab_id, original_id)

    def test_remove_tab_refuses_to_remove_the_last_tab(self):
        controller = self.make_controller()
        only_tab_id = controller.document.tabs[0].id
        removed = controller.remove_tab(only_tab_id)
        self.assertFalse(removed)
        self.assertEqual(len(controller.document.tabs), 1)

    def test_remove_active_tab_falls_back_to_a_remaining_tab(self):
        controller = self.make_controller()
        first_tab_id = controller.document.tabs[0].id
        second_tab = controller.add_tab("Second")
        controller.set_active_tab(second_tab.id)
        controller.remove_tab(second_tab.id)
        self.assertEqual(controller.active_tab_id, first_tab_id)


class PersistenceTests(ControllerTestCase):
    def test_changes_survive_a_reload_from_disk(self):
        controller = self.make_controller()
        controller.add_brush("A")
        controller.set_columns(6)

        reloaded = self.make_controller()
        grid = reloaded.active_grid()
        self.assertEqual(grid.columns, 6)
        self.assertEqual(grid.items[0].payload["brush_name"], "A")

    def test_alias_icon_forces_action_col_span_to_one_on_load(self):
        # normalize_action_spans() runs in __init__ and should shrink an
        # existing action item to col_span=1 once its alias gets an icon.
        controller = self.make_controller()
        controller.add_action("iconified.action")
        item_id = controller.active_grid().items[0].id
        controller.resize_item(item_id, col_span=3)
        self.alias_repository.save(
            {"actions": {"iconified.action": {"icon_name": "foo.png"}}, "dockers": {}}
        )

        reloaded = self.make_controller()
        self.assertEqual(reloaded.active_grid().items[0].col_span, 1)

    def test_action_text_button_can_stay_one_by_one_after_property_update_and_reload(self):
        controller = self.make_controller()
        controller.add_action("text.action")
        item_id = controller.active_grid().items[0].id
        controller.resize_item(item_id, col_span=1)
        controller.update_action_item(item_id)

        item = controller.active_grid().items[0]
        self.assertEqual(item.col_span, 1)

        reloaded = self.make_controller()
        self.assertEqual(reloaded.active_grid().items[0].col_span, 1)


class RepositoryIsolationTests(ControllerTestCase):
    def test_controller_construction_saves_only_to_the_injected_path(self):
        controller = self.make_controller()
        controller.add_brush("A")
        self.assertTrue(os.path.exists(self.repository.path))
        with open(self.repository.path, encoding="utf-8") as handle:
            data = json.load(handle)
        self.assertIn("tabs", data)

    def test_injected_repositories_never_resolve_the_real_krita_config_dir(self):
        # With no explicit path, AliasRepository/PaletteRepository resolve a
        # path under the real Krita data dir (derived from the plugin's
        # on-disk install location - see infrastructure/paths.py) and create
        # it on first use. Passing explicit paths, as make_controller() does,
        # must avoid that call entirely.
        with mock.patch(
            "quick_access_manager.remaster.infrastructure.paths.get_remaster_config_dir",
            side_effect=AssertionError("touched the real Krita config dir"),
        ):
            controller = self.make_controller()
            controller.add_brush("A")
            controller.set_columns(6)


if __name__ == "__main__":
    unittest.main()
