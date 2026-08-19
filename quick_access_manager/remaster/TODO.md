# Quick Access Palette Remaster TODO

## Immediate Verification

- [X] Verify in Krita that the popup closes when the popup itself has focus and the assigned shortcut is pressed again.
- [X] Verify popup placement against the legacy behavior on multi-monitor and near-screen-edge cursor positions.
- [X] Verify Docker icon size and Popup icon size settings after Krita restart.

## Popup

- [ ] Add screen-edge clamping so the cursor-centered popup never opens partly outside the visible screen.
- [ ] Decide whether Pin state should be runtime-only or persisted in config.
- [ ] Add optional popup width/height settings if icon-size-only control is not enough.

## Palette Item Types

- [X] Implement Docker toggle items.
- [X] Implement color picker / color swatch items.
- [X] Implement script file execution items.
- [X] Decide each new item type's default size, icon, payload schema, and config dialog fields.

## Grid Editing

- [ ] Add drag resize handles for Label and Separator width changes in Grid Edit.
- [ ] Improve multi-select UX in Grid Edit, including selection marquee or Shift/Ctrl behavior if needed.
- [ ] Add visual invalid/overflow markers in normal Docker view when column reduction leaves items outside the grid.
- [ ] Add undo/cancel safety around Grid Edit changes if editing flows become more complex.

## Tabs And Config

- [ ] Consider per-tab or per-grid column settings UI if one global active-grid column control becomes confusing.
- [ ] Add explicit tab ordering/reorder support.
- [ ] Confirm whether tab removal should ask for confirmation when the tab contains items.

## Action / Label Properties

- [ ] Add icon preview to the Action property dialog.
- [ ] Add a clear-icon option to the Action property dialog.
- [ ] Consider shared color-button helper for Action and Label property dialogs.

## Packaging / Cleanup

- [ ] Update `SPEC.md` so it matches current decisions: no UseGlobalSetting, Label/Separator width-only resize, popup shortcut behavior, and new settings tabs.
- [ ] Review `actions.action` placement and confirm Krita reliably discovers it from the remaster folder.
- [ ] Add lightweight model/layout tests that can run outside Krita.