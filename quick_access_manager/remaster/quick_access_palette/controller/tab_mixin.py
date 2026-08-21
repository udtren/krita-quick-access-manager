"""Tab lookup/selection/CRUD for the Quick Access Palette controller."""

from ...shared import PaletteGrid


class TabMixin:
    """Requires `self.document`, `self.save()`, and `self._new_id()` from the
    composed controller."""

    @property
    def active_tab_id(self) -> str | None:
        return self.document.active_tab_id

    def active_tab(self):
        if self.document.active_tab_id:
            for tab in self.document.tabs:
                if tab.id == self.document.active_tab_id:
                    return tab
        if self.document.tabs:
            self.document.active_tab_id = self.document.tabs[0].id
            return self.document.tabs[0]
        return None

    def active_grid(self) -> PaletteGrid | None:
        tab = self.active_tab()
        if not tab or not tab.grids:
            return None
        return tab.grids[0]

    def set_active_tab(self, tab_id: str):
        if any(tab.id == tab_id for tab in self.document.tabs):
            self.document.active_tab_id = tab_id
            self.save()

    def add_tab(self, name: str):
        tab_id = self._new_id("tab")
        grid = PaletteGrid(id=self._new_id("grid"), name="Main", columns=8, items=[])
        from ...shared import PaletteTab

        tab = PaletteTab(id=tab_id, name=name, grids=[grid])
        self.document.tabs.append(tab)
        self.document.active_tab_id = tab_id
        self.save()
        return tab

    def rename_tab(self, tab_id: str, name: str):
        for tab in self.document.tabs:
            if tab.id == tab_id:
                tab.name = name
                self.save()
                return tab
        raise ValueError(f"Palette tab not found: {tab_id}")

    def remove_tab(self, tab_id: str):
        if len(self.document.tabs) <= 1:
            return False
        self.document.tabs = [tab for tab in self.document.tabs if tab.id != tab_id]
        if self.document.active_tab_id == tab_id:
            self.document.active_tab_id = (
                self.document.tabs[0].id if self.document.tabs else None
            )
        self.save()
        return True
