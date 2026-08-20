"""Pure layout/model tests - no krita, no Qt, no filesystem."""

import unittest

from quick_access_manager.remaster.shared import (
    ACTION_ITEM,
    BRUSH_SIZE_ITEM,
    DEFAULT_V_SEPARATOR_ROW_SPAN,
    SEPARATOR_ITEM,
    SEPARATOR_ORIENTATION_HORIZONTAL,
    SEPARATOR_ORIENTATION_VERTICAL,
    FreeGridLayoutEngine,
    PaletteItem,
)


def brush(item_id, row=0, col=0):
    return PaletteItem.create_brush(item_id, f"brush-{item_id}", row=row, col=col)


class AddItemTests(unittest.TestCase):
    def test_add_to_empty_grid_lands_where_requested(self):
        engine = FreeGridLayoutEngine(columns=4)
        result = engine.add_item([], brush("a", row=0, col=0))
        self.assertTrue(result.valid)
        self.assertEqual((result.items[0].row, result.items[0].col), (0, 0))

    def test_add_on_top_of_existing_item_pushes_it_to_next_free_cell(self):
        engine = FreeGridLayoutEngine(columns=2)
        existing = [brush("a", row=0, col=0)]
        result = engine.add_item(existing, brush("b", row=0, col=0))
        self.assertTrue(result.valid)
        by_id = {item.id: item for item in result.items}
        # The new item claims the requested cell; the old one is pushed to
        # the next free slot in reading order (row 0 col 1).
        self.assertEqual((by_id["b"].row, by_id["b"].col), (0, 0))
        self.assertEqual((by_id["a"].row, by_id["a"].col), (0, 1))

    def test_add_duplicate_id_raises(self):
        engine = FreeGridLayoutEngine(columns=4)
        existing = [brush("a")]
        with self.assertRaises(ValueError):
            engine.add_item(existing, brush("a", row=1))

    def test_item_wider_than_grid_is_flagged_too_wide(self):
        engine = FreeGridLayoutEngine(columns=2)
        wide_action = PaletteItem.create_action("a", "action.id", col_span=3)
        result = engine.add_item([], wide_action)
        self.assertFalse(result.valid)
        self.assertEqual(result.issues[0].code, "too_wide")


class MoveItemTests(unittest.TestCase):
    def test_move_to_empty_cell(self):
        engine = FreeGridLayoutEngine(columns=4)
        items = [brush("a", row=0, col=0)]
        result = engine.move_item(items, "a", row=1, col=2)
        self.assertTrue(result.valid)
        self.assertEqual((result.items[0].row, result.items[0].col), (1, 2))

    def test_move_onto_occupied_cell_pushes_the_occupant(self):
        engine = FreeGridLayoutEngine(columns=2)
        items = [brush("a", row=0, col=0), brush("b", row=0, col=1)]
        result = engine.move_item(items, "a", row=0, col=1)
        by_id = {item.id: item for item in result.items}
        self.assertEqual((by_id["a"].row, by_id["a"].col), (0, 1))
        # b can no longer stay at (0, 1); it lands on the next free cell.
        self.assertNotEqual((by_id["b"].row, by_id["b"].col), (0, 1))
        self.assertTrue(engine.validate(result.items).valid)

    def test_move_unknown_item_raises(self):
        engine = FreeGridLayoutEngine(columns=4)
        with self.assertRaises(ValueError):
            engine.move_item([brush("a")], "missing", row=0, col=0)


class ResizeItemTests(unittest.TestCase):
    def test_resize_col_span_pushes_overlapping_neighbor(self):
        # Brush items are pinned to 1x1 (see PaletteItemModelTests below), so
        # resizing needs a type that actually supports a wider col_span.
        engine = FreeGridLayoutEngine(columns=4)
        items = [
            PaletteItem.create_label("a", "Label A", row=0, col=0, col_span=1),
            brush("b", row=0, col=1),
        ]
        result = engine.resize_item(items, "a", col_span=2)
        by_id = {item.id: item for item in result.items}
        self.assertEqual(by_id["a"].col_span, 2)
        self.assertTrue(engine.validate(result.items).valid)


class ValidateTests(unittest.TestCase):
    def test_overlap_is_reported_on_both_items(self):
        engine = FreeGridLayoutEngine(columns=4)
        items = [brush("a", row=0, col=0), brush("b", row=0, col=0)]
        result = engine.validate(items)
        self.assertFalse(result.valid)
        issues_by_item = result.issues_by_item()
        self.assertIn("a", issues_by_item)
        self.assertIn("b", issues_by_item)
        self.assertEqual(issues_by_item["a"][0].code, "overlap")

    def test_negative_position_is_flagged(self):
        engine = FreeGridLayoutEngine(columns=4)
        result = engine.validate([brush("a", row=-1, col=0)])
        self.assertFalse(result.valid)
        self.assertEqual(result.issues[0].code, "negative_position")

    def test_column_overflow_is_flagged(self):
        engine = FreeGridLayoutEngine(columns=4)
        action = PaletteItem.create_action("a", "action.id", col=3, col_span=2)
        result = engine.validate([action])
        self.assertFalse(result.valid)
        self.assertEqual(result.issues[0].code, "overflow")

    def test_no_issues_on_a_clean_grid(self):
        engine = FreeGridLayoutEngine(columns=4)
        items = [brush("a", row=0, col=0), brush("b", row=0, col=1)]
        self.assertTrue(engine.validate(items).valid)


class CompactTests(unittest.TestCase):
    def test_compact_packs_items_left_to_right_without_holes(self):
        engine = FreeGridLayoutEngine(columns=4)
        items = [brush("a", row=2, col=3), brush("b", row=5, col=0)]
        result = engine.compact(items)
        self.assertTrue(result.valid)
        positions = sorted((item.row, item.col) for item in result.items)
        self.assertEqual(positions, [(0, 0), (0, 1)])

    def test_compact_preserves_an_item_wider_than_the_grid(self):
        engine = FreeGridLayoutEngine(columns=2)
        action = PaletteItem.create_action("a", "action.id", col_span=5)
        result = engine.compact([action])
        self.assertEqual(result.items[0].col_span, 5)


class OccupiedCellsTests(unittest.TestCase):
    def test_occupied_cells_maps_every_covered_cell_to_its_item(self):
        engine = FreeGridLayoutEngine(columns=4)
        action = PaletteItem.create_action("a", "action.id", row=0, col=0, col_span=2)
        occupied = engine.occupied_cells([action])
        self.assertEqual(occupied[(0, 0)], "a")
        self.assertEqual(occupied[(0, 1)], "a")
        self.assertNotIn((0, 2), occupied)


class PaletteItemModelTests(unittest.TestCase):
    def test_unsupported_type_raises(self):
        with self.assertRaises(ValueError):
            PaletteItem(id="x", type="not-a-real-type", row=0, col=0)

    def test_brush_item_is_forced_to_a_single_cell(self):
        item = PaletteItem(
            id="x", type="brush", row=0, col=0, row_span=3, col_span=3
        )
        self.assertEqual((item.row_span, item.col_span), (1, 1))

    def test_action_col_span_defaults_and_can_be_overridden(self):
        default_span = PaletteItem.create_action("a", "some.action.id")
        self.assertEqual(default_span.type, ACTION_ITEM)
        self.assertGreaterEqual(default_span.col_span, 2)
        wide = PaletteItem.create_action("a", "action.id", col_span=4)
        self.assertEqual(wide.col_span, 4)


class SeparatorOrientationTests(unittest.TestCase):
    def test_horizontal_separator_defaults_span_the_width_axis(self):
        item = PaletteItem.create_separator("s")
        self.assertEqual(item.type, SEPARATOR_ITEM)
        self.assertEqual(item.payload.get("orientation"), SEPARATOR_ORIENTATION_HORIZONTAL)
        self.assertEqual(item.row_span, 1)
        self.assertGreaterEqual(item.col_span, 1)

    def test_vertical_separator_defaults_span_the_height_axis(self):
        item = PaletteItem.create_separator("s", orientation=SEPARATOR_ORIENTATION_VERTICAL)
        self.assertEqual(item.payload.get("orientation"), SEPARATOR_ORIENTATION_VERTICAL)
        self.assertEqual(item.col_span, 1)
        self.assertEqual(item.row_span, DEFAULT_V_SEPARATOR_ROW_SPAN)

    def test_vertical_separator_col_span_is_pinned_to_one_even_if_requested_wider(self):
        item = PaletteItem.create_separator(
            "s", orientation=SEPARATOR_ORIENTATION_VERTICAL, col_span=5
        )
        self.assertEqual(item.col_span, 1)

    def test_horizontal_separator_row_span_is_pinned_to_one_even_if_requested_taller(self):
        item = PaletteItem.create_separator(
            "s", orientation=SEPARATOR_ORIENTATION_HORIZONTAL, row_span=5
        )
        self.assertEqual(item.row_span, 1)

    def test_a_tall_vertical_separator_does_not_corrupt_placement_of_other_items(self):
        # Regression check for the "does placement logic need a rewrite"
        # question: a multi-row item should just occupy its real footprint,
        # with no special-casing anywhere in the engine.
        engine = FreeGridLayoutEngine(columns=3)
        tall = PaletteItem.create_separator(
            "sep", row=0, col=0, orientation=SEPARATOR_ORIENTATION_VERTICAL
        )
        result = engine.add_item([], tall)
        self.assertTrue(result.valid)
        occupied = engine.occupied_cells(result.items)
        self.assertEqual(
            {cell for cell, item_id in occupied.items() if item_id == "sep"},
            {(0, 0), (1, 0), (2, 0)},
        )

        # A second item requested directly inside the separator's footprint
        # claims that cell (the engine always honors a new item's requested
        # position - see AddItemTests.test_add_on_top_of_existing_item_*);
        # the separator is the one that gets pushed elsewhere, and the result
        # is still a fully valid, non-overlapping layout.
        result = engine.add_item(result.items, brush("b", row=1, col=0))
        self.assertTrue(engine.validate(result.items).valid)
        by_id = {item.id: item for item in result.items}
        self.assertEqual((by_id["b"].row, by_id["b"].col), (1, 0))
        self.assertNotEqual((by_id["sep"].row, by_id["sep"].col), (0, 0))


class BrushSizeItemTests(unittest.TestCase):
    def test_create_brush_size_is_a_fixed_one_by_one_cell(self):
        item = PaletteItem.create_brush_size("bs", "25")
        self.assertEqual(item.type, BRUSH_SIZE_ITEM)
        self.assertEqual((item.row_span, item.col_span), (1, 1))
        self.assertEqual(item.payload.get("text"), "25")

    def test_create_brush_size_merges_style_config_into_payload(self):
        item = PaletteItem.create_brush_size(
            "bs",
            "10",
            config={
                "fontSize": "22",
                "backgroundColor": "#112233",
                "fontColor": "#445566",
            },
        )
        self.assertEqual(item.payload["text"], "10")
        self.assertEqual(item.payload["fontSize"], "22")
        self.assertEqual(item.payload["backgroundColor"], "#112233")
        self.assertEqual(item.payload["fontColor"], "#445566")

    def test_add_brush_size_participates_in_normal_grid_placement(self):
        engine = FreeGridLayoutEngine(columns=4)
        first = PaletteItem.create_brush_size("bs1", "10", row=0, col=0)
        result = engine.add_item([], first)
        second = PaletteItem.create_brush_size("bs2", "25", row=0, col=0)
        result = engine.add_item(result.items, second)
        self.assertTrue(engine.validate(result.items).valid)
        by_id = {item.id: item for item in result.items}
        self.assertEqual((by_id["bs2"].row, by_id["bs2"].col), (0, 0))
        self.assertNotEqual((by_id["bs1"].row, by_id["bs1"].col), (0, 0))


if __name__ == "__main__":
    unittest.main()
