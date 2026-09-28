"""Concrete Flet Builder screen backed by the tested domain and persistence layers."""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from collections.abc import Callable
from copy import deepcopy
from pathlib import Path
from typing import Any
from uuid import UUID

from .builder import TeamEditor
from .flet_helpers import event_handler, flet_module, text_value_handler
from .models import Team, TeamList, TraitSelection
from .persistence import AutosaveService
from .search import normalize_search_text
from .set_display import (
    asset_source,
    champion_details_text,
    champion_matches_query,
    champion_trait_ids,
    localized_text,
)
from .set_loader import LoadedSet
from .set_schema import (
    ChampionDefinition,
    DynamicSelectionRule,
    DynamicSelectionScope,
    DynamicTraitDefinition,
)
from .trait_engine import (
    TraitCalculationResult,
    TraitResult,
    calculate_traits,
    validate_dynamic_selection,
)

_TEXT_SAVE_DELAY_SECONDS = 0.45
_DRAG_GROUP = "builder-champion"


def filtered_champion_groups(
    loaded_set: LoadedSet,
    query: str,
    *,
    trait_filter_id: str | None = None,
) -> tuple[tuple[int, tuple[ChampionDefinition, ...]], ...]:
    """Filter the catalog by Champion text, Trait text and optional clicked-Trait filter."""

    search_key = normalize_search_text(query)
    grouped: dict[int, list[ChampionDefinition]] = defaultdict(list)
    for champion in loaded_set.champions:
        trait_ids = champion_trait_ids(loaded_set, champion)
        if trait_filter_id is not None and trait_filter_id not in trait_ids:
            continue
        if search_key and not champion_matches_query(loaded_set, champion, query):
            continue
        grouped[champion.cost].append(champion)

    return tuple(
        (
            cost,
            tuple(sorted(grouped[cost], key=lambda item: (item.display_order, item.id))),
        )
        for cost in sorted(grouped)
    )


def parse_drag_source_key(key: Any) -> tuple[str, str | UUID] | None:
    """Decode one stable Draggable key without relying on control object identity."""

    if not isinstance(key, str):
        return None
    if key.startswith("drag-library-"):
        champion_id = key.removeprefix("drag-library-")
        return ("library", champion_id) if champion_id else None
    if key.startswith("drag-instance-"):
        raw_id = key.removeprefix("drag-instance-")
        try:
            return "instance", UUID(raw_id)
        except ValueError:
            return None
    return None


def dynamic_rule_summary(rule: DynamicTraitDefinition) -> str:
    """Return concise user-facing cardinality text for one validated dynamic rule."""

    if rule.selection_rule is DynamicSelectionRule.EXACTLY_ONE:
        return "Choose exactly one Trait."
    if rule.selection_rule is DynamicSelectionRule.ZERO_OR_ONE:
        return "Choose zero or one Trait."
    if rule.selection_rule is DynamicSelectionRule.ANY_NUMBER:
        return "Choose any number of Traits."
    if rule.selection_rule is DynamicSelectionRule.EXACTLY_N:
        return f"Choose exactly {rule.exact_count} Traits."
    return "This Champion does not require a dynamic Trait choice."


def reconcile_active_list(team: Team, active_list_id: UUID) -> UUID:
    """Keep valid transient navigation or fall back to the persisted primary List."""

    if any(team_list.list_id == active_list_id for team_list in team.lists):
        return active_list_id
    return team.primary_list_id


def visible_trait_results(
    calculation: TraitCalculationResult, *, hide_below_first_breakpoint: bool
) -> tuple[TraitResult, ...]:
    """Apply the Builder's presentation-only Trait visibility preference."""

    if not hide_below_first_breakpoint:
        return calculation.traits
    return tuple(trait for trait in calculation.traits if trait.active_breakpoint is not None)


class BuilderView:
    """Imperative desktop Builder composition with transient navigation/preferences."""

    def __init__(
        self,
        page: Any,
        loaded_set: LoadedSet,
        editor: TeamEditor,
        autosave: AutosaveService,
        *,
        assets_dir: Path,
        on_back: Callable[[], None] | None = None,
    ) -> None:
        if not isinstance(loaded_set, LoadedSet):
            raise TypeError("loaded_set must be a LoadedSet")
        if not isinstance(editor, TeamEditor):
            raise TypeError("editor must be a TeamEditor")
        if not isinstance(autosave, AutosaveService):
            raise TypeError("autosave must be an AutosaveService")
        self.page = page
        self.loaded_set = loaded_set
        self.editor = editor
        self.autosave = autosave
        self.assets_dir = Path(assets_dir).resolve()
        self.on_back = on_back
        self.active_list_id = editor.team.primary_list_id
        self.hide_below_first_breakpoint = False
        self.show_next_breakpoint_progress = True
        self.champion_search_query = ""
        self.trait_filter_id: str | None = None
        self.status_message = "Saved"
        self.status_is_error = False
        self.status_is_pending = False
        self._root: Any | None = None
        self._undo_button: Any | None = None
        self._redo_button: Any | None = None
        self._status_indicator: Any | None = None
        self._champion_search_field: Any | None = None
        self._champion_results: Any | None = None
        self._open_dialog: Any | None = None
        self._text_input_focused = False
        self._text_save_revision = 0
        self._champions_by_id = self.loaded_set.champions_by_id
        self._traits_by_id = self.loaded_set.traits_by_id
        self._dynamic_by_champion = {
            rule.champion_id: rule for rule in self.loaded_set.dynamic_traits
        }
        self._logger = logging.getLogger("tft_builder.builder_view")

    @property
    def team(self) -> Team:
        return self.editor.team

    @property
    def active_list(self) -> TeamList:
        self.active_list_id = reconcile_active_list(self.team, self.active_list_id)
        return next(
            team_list for team_list in self.team.lists if team_list.list_id == self.active_list_id
        )

    def mount(self) -> None:
        """Attach the complete Builder screen to its Page."""

        ft = flet_module()
        self.page.title = "TFT Team Builder"
        self.page.on_keyboard_event = self._handle_keyboard_event
        self._root = ft.SafeArea(expand=True, content=self._build_layout())
        self.page.add(self._root)

    def refresh(self) -> None:
        """Rebuild screen controls after structural state changes."""

        self.active_list_id = reconcile_active_list(self.team, self.active_list_id)
        self._text_input_focused = False
        if self._root is not None:
            self._root.content = self._build_layout()
            self.page.update()

    def select_list(self, list_id: UUID) -> None:
        """Change only transient Builder navigation state."""

        if not any(team_list.list_id == list_id for team_list in self.team.lists):
            raise ValueError(f"unknown List ID: {list_id}")
        self.active_list_id = list_id
        self.refresh()

    def create_list(self) -> None:
        name = f"List {len(self.team.lists) + 1}"
        created: UUID | None = None

        def action() -> None:
            nonlocal created
            created = self.editor.create_list(name)

        if self._run_structural("Create List", action):
            self.active_list_id = created
            self.refresh()

    def duplicate_list(self, list_id: UUID) -> None:
        created: UUID | None = None

        def action() -> None:
            nonlocal created
            created = self.editor.duplicate_list(list_id, name=f"{self._list(list_id).name} Copy")

        if self._run_structural("Duplicate List", action):
            self.active_list_id = created
            self.refresh()

    def delete_list(self, list_id: UUID) -> None:
        self._run_structural("Delete List", lambda: self.editor.delete_list(list_id))

    def reorder_list(self, list_id: UUID, new_index: int) -> None:
        self._run_structural("Reorder List", lambda: self.editor.reorder_list(list_id, new_index))

    def clear_list(self, list_id: UUID) -> None:
        self._run_structural("Clear List", lambda: self.editor.clear_list(list_id))

    def compact_list(self, list_id: UUID) -> None:
        self._run_structural("Compact List", lambda: self.editor.compact_list(list_id))

    def set_primary_list(self, list_id: UUID) -> None:
        self._run_structural("Set primary List", lambda: self.editor.set_primary_list(list_id))

    def add_champion(self, champion_id: str) -> bool:
        return self.add_champion_to_list(self.active_list_id, champion_id)

    def add_champion_to_list(self, list_id: UUID, champion_id: str) -> bool:
        """Append one new Champion instance to a concrete List."""

        return self._run_structural(
            "Add Champion",
            lambda: self.editor.add_champion(
                list_id,
                len(self._list(list_id).slots),
                champion_id,
            ),
        )

    def remove_champion(self, list_id: UUID, slot_index: int) -> None:
        """Remove the occupied GUI slot so the remaining Champion row closes the gap."""

        self._run_structural(
            "Remove Champion", lambda: self.editor.remove_slot(list_id, slot_index)
        )

    def copy_champion_to_active(self, source_list_id: UUID, source_index: int) -> None:
        """Copy one placed Champion to the end of the active List with a new instance ID."""

        self._run_structural(
            "Copy Champion",
            lambda: self.editor.copy_champion(
                source_list_id,
                source_index,
                self.active_list_id,
                len(self.active_list.slots),
            ),
        )

    def undo(self) -> None:
        self._run_structural("Undo", self.editor.undo)

    def redo(self) -> None:
        self._run_structural("Redo", self.editor.redo)

    def rename_team(self, name: str) -> bool:
        return self._run_text_edit("Rename Team", lambda: self.editor.rename_team(name))

    def rename_list(self, list_id: UUID, name: str) -> bool:
        return self._run_text_edit("Rename List", lambda: self.editor.rename_list(list_id, name))

    def flush_text(self) -> bool:
        """Invalidate pending debounce tasks and synchronously persist queued text state."""

        self._text_save_revision += 1
        try:
            self.autosave.flush(self.team.team_id)
        except Exception as error:
            self._save_failed("text flush", error)
            return False
        self._set_status("Saved")
        return True

    def back_to_library(self) -> None:
        """Flush queued edits before leaving the Builder; stay put if persistence fails."""

        if self.on_back is not None and self.flush_text():
            self.on_back()

    def set_hide_below_first_breakpoint(self, value: bool) -> None:
        self.hide_below_first_breakpoint = bool(value)
        self.refresh()

    def set_show_next_breakpoint_progress(self, value: bool) -> None:
        self.show_next_breakpoint_progress = bool(value)
        self.refresh()

    def set_champion_search(self, value: str) -> None:
        """Update only the Champion results so typing keeps keyboard focus."""

        self.champion_search_query = value
        self._refresh_champion_results()

    def toggle_trait_filter(self, trait_id: str) -> None:
        """Toggle one Trait as a transient Champion-library filter."""

        if trait_id not in self._traits_by_id:
            raise ValueError(f"unknown Trait ID: {trait_id}")
        self.trait_filter_id = None if self.trait_filter_id == trait_id else trait_id
        self.refresh()

    def clear_trait_filter(self) -> None:
        if self.trait_filter_id is not None:
            self.trait_filter_id = None
            self.refresh()

    def open_dynamic_selection(self, list_id: UUID, slot_index: int) -> None:
        """Open one validated dynamic Trait editor for the placed Champion."""

        team_list = self._list(list_id)
        if slot_index < 0 or slot_index >= len(team_list.slots):
            raise IndexError("dynamic Trait slot index is outside the List")
        champion = team_list.slots[slot_index].champion
        if champion is None:
            raise ValueError("dynamic Trait slot does not contain a Champion")
        rule = self._dynamic_by_champion.get(champion.champion_id)
        if rule is None:
            raise ValueError("Champion does not have an editable dynamic Trait rule")
        self._show_dynamic_selection_dialog(list_id, slot_index, rule)

    def open_dynamic_selection_by_instance(self, instance_id: UUID) -> None:
        list_id, slot_index = self._locate_instance(instance_id)
        self.open_dynamic_selection(list_id, slot_index)

    def _run_structural(self, label: str, action: Callable[[], Any]) -> bool:
        self._text_save_revision += 1
        before = deepcopy(self.team)
        try:
            action()
        except Exception as error:
            self._action_failed(label, error)
            self.refresh()
            return False

        if self.team == before:
            self._sync_history_controls()
            return False

        self.active_list_id = reconcile_active_list(self.team, self.active_list_id)
        try:
            self.autosave.save_now(self.team)
        except Exception as error:
            self.autosave.queue(self.team)
            self._save_failed(label, error)
        else:
            self._set_status("Saved")
        self.refresh()
        return True

    def _run_text_edit(self, label: str, action: Callable[[], bool]) -> bool:
        try:
            changed = action()
        except Exception as error:
            self._action_failed(label, error)
            return False
        if not changed:
            return False
        self.autosave.queue(self.team)
        self._set_status("Saving changes", pending=True)
        self._sync_history_controls()
        self._text_save_revision += 1
        self.page.run_task(self._debounced_text_flush, self._text_save_revision)
        return True

    async def _debounced_text_flush(self, revision: int) -> None:
        await asyncio.sleep(_TEXT_SAVE_DELAY_SECONDS)
        if revision != self._text_save_revision:
            return
        try:
            await asyncio.to_thread(self.autosave.flush, self.team.team_id)
        except Exception as error:
            self._save_failed("debounced text save", error)
        else:
            self._set_status("Saved")
        self.page.update()

    def _action_failed(self, label: str, error: Exception) -> None:
        self._logger.warning("%s failed: %s", label, error)
        self._set_status(f"{label} failed: {error}", error=True)

    def _save_failed(self, label: str, error: Exception) -> None:
        self._logger.exception("Persistence failed after %s", label, exc_info=error)
        self._set_status(f"Save failed after {label}: {error}", error=True)

    def _set_status(self, message: str, *, error: bool = False, pending: bool = False) -> None:
        self.status_message = message
        self.status_is_error = error
        self.status_is_pending = pending and not error
        if self._status_indicator is not None:
            ft = flet_module()
            self._status_indicator.tooltip = message
            self._status_indicator.content.icon = self._status_icon(ft)
            self._status_indicator.content.color = self._status_color(ft)

    def _status_icon(self, ft: Any) -> Any:
        if self.status_is_error:
            return ft.Icons.ERROR_OUTLINE
        if self.status_is_pending:
            return ft.Icons.SYNC
        return ft.Icons.CHECK_CIRCLE_OUTLINE

    def _status_color(self, ft: Any) -> Any:
        if self.status_is_error:
            return ft.Colors.ERROR
        if self.status_is_pending:
            return ft.Colors.PRIMARY
        return ft.Colors.ON_SURFACE_VARIANT

    def _sync_history_controls(self) -> None:
        if self._undo_button is not None:
            self._undo_button.disabled = not self.editor.can_undo
        if self._redo_button is not None:
            self._redo_button.disabled = not self.editor.can_redo

    def _list(self, list_id: UUID) -> TeamList:
        for team_list in self.team.lists:
            if team_list.list_id == list_id:
                return team_list
        raise ValueError(f"unknown List ID: {list_id}")

    def _locate_instance(self, instance_id: UUID) -> tuple[UUID, int]:
        if not isinstance(instance_id, UUID):
            raise TypeError("instance_id must be a UUID")
        for team_list in self.team.lists:
            for slot in team_list.slots:
                if slot.champion is not None and slot.champion.instance_id == instance_id:
                    return team_list.list_id, slot.index
        raise ValueError(f"unknown Champion instance ID: {instance_id}")

    def _build_layout(self) -> Any:
        ft = flet_module()
        toolbar = self._build_toolbar(ft)
        body = ft.Row(
            expand=True,
            vertical_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=[
                ft.Container(
                    width=280,
                    padding=12,
                    bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
                    content=self._build_traits(ft),
                ),
                ft.VerticalDivider(width=1),
                ft.Container(expand=True, padding=12, content=self._build_lists(ft)),
                ft.VerticalDivider(width=1),
                ft.Container(
                    width=340,
                    padding=12,
                    bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
                    content=self._build_champions(ft),
                ),
            ],
        )
        return ft.Column(expand=True, controls=[toolbar, ft.Divider(height=1), body])

    def _build_toolbar(self, ft: Any) -> Any:
        team_name = ft.TextField(
            key="builder-team-name",
            value=self.team.name,
            label="Team name",
            expand=True,
            on_change=self._name_change_handler(self.rename_team),
            on_focus=self._focus_handler(True),
            on_blur=self._name_finish_handler(self.rename_team),
            on_submit=self._name_finish_handler(self.rename_team),
        )
        self._undo_button = ft.Button(
            key="builder-undo",
            content="Undo",
            icon=ft.Icons.UNDO,
            disabled=not self.editor.can_undo,
            on_click=event_handler(self.undo),
        )
        self._redo_button = ft.Button(
            key="builder-redo",
            content="Redo",
            icon=ft.Icons.REDO,
            disabled=not self.editor.can_redo,
            on_click=event_handler(self.redo),
        )
        self._status_indicator = ft.Container(
            key="builder-save-status",
            width=40,
            height=40,
            alignment=ft.Alignment.CENTER,
            tooltip=self.status_message,
            content=ft.Icon(icon=self._status_icon(ft), color=self._status_color(ft), size=20),
        )
        return ft.Container(
            padding=8,
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            border_radius=10,
            content=ft.Row(
                controls=[
                    *(
                        [
                            ft.IconButton(
                                key="builder-back",
                                icon=ft.Icons.ARROW_BACK,
                                tooltip="Back to Team Library",
                                on_click=event_handler(self.back_to_library),
                            )
                        ]
                        if self.on_back is not None
                        else []
                    ),
                    team_name,
                    ft.Button(
                        key="builder-new-list",
                        content="New List",
                        icon=ft.Icons.ADD,
                        on_click=event_handler(self.create_list),
                    ),
                    self._undo_button,
                    self._redo_button,
                    self._status_indicator,
                ]
            ),
        )

    def _build_traits(self, ft: Any) -> Any:
        calculation = calculate_traits(self.loaded_set, self.active_list)
        controls: list[Any] = [
            ft.Text("Traits", size=22, weight=ft.FontWeight.BOLD),
            ft.Checkbox(
                key="builder-hide-below-breakpoint",
                label="Hide below first breakpoint",
                value=self.hide_below_first_breakpoint,
                on_change=self._bool_handler(self.set_hide_below_first_breakpoint),
            ),
            ft.Checkbox(
                key="builder-show-next-breakpoint",
                label="Show next breakpoint progress",
                value=self.show_next_breakpoint_progress,
                on_change=self._bool_handler(self.set_show_next_breakpoint_progress),
            ),
        ]
        if calculation.dynamic_issues:
            first_issue = calculation.dynamic_issues[0]
            issue_controls: list[Any] = [
                ft.Text("Dynamic Trait selection required", weight=ft.FontWeight.BOLD),
                *[ft.Text(issue.message) for issue in calculation.dynamic_issues],
            ]
            issue_controls.append(
                ft.Button(
                    key="builder-fix-dynamic",
                    content="Choose Traits",
                    icon=ft.Icons.TUNE,
                    on_click=event_handler(
                        self.open_dynamic_selection_by_instance,
                        first_issue.instance_ids[0],
                    ),
                )
            )
            controls.append(
                ft.Container(
                    key="builder-dynamic-issues",
                    padding=8,
                    border=ft.Border.all(1, ft.Colors.ERROR),
                    border_radius=8,
                    content=ft.Column(controls=issue_controls),
                )
            )
        for result in visible_trait_results(
            calculation,
            hide_below_first_breakpoint=self.hide_below_first_breakpoint,
        ):
            controls.append(self._build_trait_row(ft, result))
        if len(controls) == 3:
            controls.append(ft.Text("No active Trait contributions."))
        return ft.ListView(expand=True, spacing=8, controls=controls)

    def _build_trait_row(self, ft: Any, result: TraitResult) -> Any:
        definition = self._traits_by_id[result.trait_id]
        details = [f"Count: {result.count}"]
        if result.active_breakpoint is not None:
            details.append(
                f"Active: {result.active_breakpoint.count} ({result.active_breakpoint.style})"
            )
        if self.show_next_breakpoint_progress and result.next_breakpoint is not None:
            details.append(
                f"Next: {result.next_breakpoint.count} ({result.needed_for_next_breakpoint} needed)"
            )
        if result.has_invalid_dynamic_selection:
            details.append("Dynamic selection invalid")
        selected = self.trait_filter_id == result.trait_id
        return ft.Container(
            key=f"trait-{result.trait_id}",
            padding=8,
            tooltip="Filter Champion Library by this Trait",
            on_click=event_handler(self.toggle_trait_filter, result.trait_id),
            bgcolor=ft.Colors.SECONDARY_CONTAINER if selected else None,
            border=ft.Border.all(
                2 if selected else 1,
                ft.Colors.PRIMARY
                if selected
                else (
                    ft.Colors.ERROR
                    if result.has_invalid_dynamic_selection
                    else ft.Colors.OUTLINE_VARIANT
                ),
            ),
            border_radius=8,
            content=ft.Row(
                controls=[
                    ft.Image(
                        src=asset_source(self.loaded_set, self.assets_dir, definition.icon),
                        width=36,
                        height=36,
                    ),
                    ft.Column(
                        expand=True,
                        spacing=2,
                        controls=[
                            ft.Text(
                                localized_text(self.loaded_set, definition.name_key),
                                weight=(
                                    ft.FontWeight.BOLD
                                    if result.active_breakpoint is not None
                                    else None
                                ),
                            ),
                            ft.Text(" | ".join(details), size=12),
                        ],
                    ),
                ]
            ),
        )

    def _build_lists(self, ft: Any) -> Any:
        return ft.ListView(
            expand=True,
            spacing=12,
            controls=[
                self._build_list_card(ft, team_list, index)
                for index, team_list in enumerate(self.team.lists)
            ],
        )

    def _build_list_card(self, ft: Any, team_list: TeamList, index: int) -> Any:
        is_active = team_list.list_id == self.active_list_id
        is_primary = team_list.list_id == self.team.primary_list_id
        actions = self._build_list_actions(ft, team_list, index, is_active, is_primary)
        slots = [
            self._build_slot(ft, team_list, slot.index)
            for slot in team_list.slots
            if slot.champion is not None
        ]
        slots.append(self._build_end_slot(ft, team_list))
        return ft.Container(
            key=f"list-{team_list.list_id}",
            padding=12,
            border=ft.Border.all(
                2 if is_active else 1,
                ft.Colors.PRIMARY if is_active else ft.Colors.OUTLINE_VARIANT,
            ),
            border_radius=10,
            bgcolor=(ft.Colors.PRIMARY_CONTAINER if is_active else ft.Colors.SURFACE_CONTAINER_LOW),
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.TextField(
                                key=f"list-name-{team_list.list_id}",
                                value=team_list.name,
                                label="List name",
                                expand=True,
                                on_change=self._name_change_handler(
                                    self.rename_list, team_list.list_id
                                ),
                                on_focus=self._focus_handler(True),
                                on_blur=self._name_finish_handler(
                                    self.rename_list, team_list.list_id
                                ),
                                on_submit=self._name_finish_handler(
                                    self.rename_list, team_list.list_id
                                ),
                            ),
                            actions,
                        ]
                    ),
                    ft.Row(scroll=ft.ScrollMode.AUTO, controls=slots),
                ]
            ),
        )

    def _build_list_actions(
        self, ft: Any, team_list: TeamList, index: int, is_active: bool, is_primary: bool
    ) -> Any:
        """Keep common navigation visible and move maintenance actions into one menu."""

        more = ft.PopupMenuButton(
            key=f"list-more-{team_list.list_id}",
            icon=ft.Icons.MORE_VERT,
            tooltip="List actions",
            items=[
                ft.PopupMenuItem(
                    key=f"list-duplicate-{team_list.list_id}",
                    content="Duplicate",
                    icon=ft.Icons.CONTENT_COPY,
                    on_click=event_handler(self.duplicate_list, team_list.list_id),
                ),
                ft.PopupMenuItem(
                    key=f"list-compact-{team_list.list_id}",
                    content="Compact gaps",
                    icon=ft.Icons.COMPRESS,
                    on_click=event_handler(self.compact_list, team_list.list_id),
                ),
                ft.PopupMenuItem(
                    key=f"list-clear-{team_list.list_id}",
                    content="Clear Champions",
                    icon=ft.Icons.CLEAR_ALL,
                    on_click=event_handler(self._confirm_clear_list, team_list.list_id),
                ),
                ft.PopupMenuItem(
                    key=f"list-delete-{team_list.list_id}",
                    content="Delete List",
                    icon=ft.Icons.DELETE_OUTLINE,
                    disabled=len(self.team.lists) == 1,
                    on_click=event_handler(self._confirm_delete_list, team_list.list_id),
                ),
            ],
        )
        return ft.Row(
            wrap=True,
            controls=[
                ft.Button(
                    content="Active" if is_active else "Open",
                    key=f"list-open-{team_list.list_id}",
                    disabled=is_active,
                    on_click=event_handler(self.select_list, team_list.list_id),
                ),
                ft.IconButton(
                    key=f"list-primary-{team_list.list_id}",
                    icon=ft.Icons.STAR if is_primary else ft.Icons.STAR_OUTLINE,
                    tooltip="Primary List",
                    on_click=event_handler(self.set_primary_list, team_list.list_id),
                ),
                ft.IconButton(
                    key=f"list-up-{team_list.list_id}",
                    icon=ft.Icons.ARROW_UPWARD,
                    disabled=index == 0,
                    tooltip="Move List up",
                    on_click=event_handler(self.reorder_list, team_list.list_id, index - 1),
                ),
                ft.IconButton(
                    key=f"list-down-{team_list.list_id}",
                    icon=ft.Icons.ARROW_DOWNWARD,
                    disabled=index == len(self.team.lists) - 1,
                    tooltip="Move List down",
                    on_click=event_handler(self.reorder_list, team_list.list_id, index + 1),
                ),
                more,
            ],
        )

    def _build_slot(self, ft: Any, team_list: TeamList, index: int) -> Any:
        slot = team_list.slots[index]
        champion = slot.champion
        definition = self._champions_by_id[champion.champion_id]
        name = localized_text(self.loaded_set, definition.name_key)
        dynamic_rule = self._dynamic_by_champion.get(champion.champion_id)
        actions: list[Any] = [
            ft.IconButton(
                key=f"slot-copy-{team_list.list_id}-{index}",
                icon=ft.Icons.CONTENT_COPY,
                icon_size=18,
                width=30,
                height=30,
                padding=0,
                tooltip="Copy to active List",
                on_click=event_handler(self.copy_champion_to_active, team_list.list_id, index),
            )
        ]
        if (
            dynamic_rule is not None
            and dynamic_rule.selection_rule is not DynamicSelectionRule.NONE
        ):
            actions.append(
                ft.IconButton(
                    key=f"slot-traits-{team_list.list_id}-{index}",
                    icon=ft.Icons.TUNE,
                    icon_size=18,
                    width=30,
                    height=30,
                    padding=0,
                    tooltip="Choose dynamic Traits",
                    on_click=event_handler(self.open_dynamic_selection, team_list.list_id, index),
                )
            )
        actions.append(
            ft.IconButton(
                key=f"slot-remove-{team_list.list_id}-{index}",
                icon=ft.Icons.REMOVE_CIRCLE_OUTLINE,
                icon_size=18,
                width=30,
                height=30,
                padding=0,
                tooltip="Remove Champion",
                on_click=event_handler(self.remove_champion, team_list.list_id, index),
            )
        )
        card = ft.Container(
            key=f"slot-{team_list.list_id}-{index}",
            width=112,
            tooltip=champion_details_text(self.loaded_set, definition),
            height=142,
            padding=6,
            bgcolor=ft.Colors.SURFACE,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=10,
            content=ft.Column(
                spacing=4,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Draggable(
                        key=f"drag-instance-{champion.instance_id}",
                        group=_DRAG_GROUP,
                        content=ft.Column(
                            spacing=2,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Image(
                                    src=asset_source(
                                        self.loaded_set,
                                        self.assets_dir,
                                        definition.image,
                                    ),
                                    width=48,
                                    height=48,
                                ),
                                ft.Text(name, size=11, max_lines=2),
                            ],
                        ),
                        content_feedback=ft.Container(
                            padding=8,
                            border_radius=8,
                            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                            content=ft.Text(name, size=12),
                        ),
                    ),
                    ft.Row(spacing=2, controls=actions),
                ],
            ),
        )
        return ft.DragTarget(
            key=f"drop-slot-{team_list.list_id}-{index}",
            group=_DRAG_GROUP,
            content=card,
            on_will_accept=self._drag_will_accept,
            on_leave=self._drag_leave,
            on_accept=self._drop_handler(self._drop_on_slot, team_list.list_id, index),
        )

    def _build_end_slot(self, ft: Any, team_list: TeamList) -> Any:
        """Render the one intentional empty position at the right edge of a List."""

        content = ft.Container(
            key=f"slot-end-{team_list.list_id}",
            width=112,
            height=142,
            alignment=ft.Alignment.CENTER,
            tooltip="Add or drop a Champion here",
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=10,
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=4,
                controls=[
                    ft.Icon(icon=ft.Icons.ADD, color=ft.Colors.ON_SURFACE_VARIANT, size=22),
                    ft.Text("Add unit", size=11, color=ft.Colors.ON_SURFACE_VARIANT),
                ],
            ),
        )
        return ft.DragTarget(
            key=f"drop-end-{team_list.list_id}",
            group=_DRAG_GROUP,
            content=content,
            on_will_accept=self._drag_will_accept,
            on_leave=self._drag_leave,
            on_accept=self._drop_handler(self._drop_on_end, team_list.list_id),
        )

    def _build_champions(self, ft: Any) -> Any:
        self._champion_search_field = ft.TextField(
            key="builder-champion-search",
            value=self.champion_search_query,
            label="Search Champions or Traits",
            on_change=text_value_handler(self.set_champion_search),
            on_focus=self._focus_handler(True),
            on_blur=self._focus_handler(False),
        )
        self._champion_results = ft.ListView(
            expand=True,
            spacing=8,
            controls=self._champion_result_controls(ft),
        )
        return ft.Column(
            expand=True,
            controls=[
                ft.Text("Champion Library", size=22, weight=ft.FontWeight.BOLD),
                self._champion_search_field,
                self._champion_results,
            ],
        )

    def _champion_result_controls(self, ft: Any) -> list[Any]:
        controls: list[Any] = []
        if self.trait_filter_id is not None:
            trait = self._traits_by_id[self.trait_filter_id]
            controls.append(
                ft.Container(
                    key="builder-trait-filter",
                    padding=6,
                    border_radius=8,
                    bgcolor=ft.Colors.SECONDARY_CONTAINER,
                    content=ft.Row(
                        controls=[
                            ft.Text(
                                f"Trait: {localized_text(self.loaded_set, trait.name_key)}",
                                expand=True,
                            ),
                            ft.IconButton(
                                key="builder-clear-trait-filter",
                                icon=ft.Icons.CLOSE,
                                icon_size=18,
                                tooltip="Clear Trait filter",
                                on_click=event_handler(self.clear_trait_filter),
                            ),
                        ]
                    ),
                )
            )

        groups = filtered_champion_groups(
            self.loaded_set,
            self.champion_search_query,
            trait_filter_id=self.trait_filter_id,
        )
        if not groups:
            controls.append(
                ft.Text(
                    "No Champions match the current search and Trait filter.",
                    key="builder-champion-empty",
                    color=ft.Colors.ON_SURFACE_VARIANT,
                )
            )
            return controls

        for cost, champions in groups:
            controls.append(ft.Text(f"Cost {cost}", size=16, weight=ft.FontWeight.BOLD))
            controls.extend(self._build_champion_card(ft, champion) for champion in champions)
        return controls

    def _refresh_champion_results(self) -> None:
        if self._champion_results is None:
            return
        self._champion_results.controls = self._champion_result_controls(flet_module())
        self.page.update()

    def _build_champion_card(self, ft: Any, champion: ChampionDefinition) -> Any:
        name = localized_text(self.loaded_set, champion.name_key)
        draggable = ft.Draggable(
            key=f"drag-library-{champion.id}",
            group=_DRAG_GROUP,
            content=ft.Row(
                expand=True,
                controls=[
                    ft.Image(
                        src=asset_source(self.loaded_set, self.assets_dir, champion.image),
                        width=48,
                        height=48,
                    ),
                    ft.Column(
                        expand=True,
                        controls=[
                            ft.Text(name),
                            ft.Text(f"Cost {champion.cost}", size=12),
                        ],
                    ),
                ],
            ),
            content_feedback=ft.Container(
                padding=8,
                border_radius=8,
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                content=ft.Text(name),
            ),
        )
        return ft.Container(
            key=f"champion-{champion.id}",
            padding=8,
            tooltip=champion_details_text(self.loaded_set, champion),
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=8,
            content=ft.Row(
                controls=[
                    draggable,
                    ft.IconButton(
                        key=f"champion-add-{champion.id}",
                        icon=ft.Icons.ADD_CIRCLE_OUTLINE,
                        tooltip="Add to active List",
                        on_click=event_handler(self.add_champion, champion.id),
                    ),
                ]
            ),
        )

    def _drop_on_slot(self, event: Any, target_list_id: UUID, target_index: int) -> bool:
        """Translate one occupied-slot drop to the existing swap/move core operation."""

        self._reset_drop_target(event)
        source = parse_drag_source_key(getattr(getattr(event, "src", None), "key", None))
        if source is None or source[0] != "instance":
            return False
        source_list_id, source_index = self._locate_instance(source[1])
        return self._run_structural(
            "Move Champion",
            lambda: self.editor.move_champion(
                source_list_id,
                source_index,
                target_list_id,
                target_index,
            ),
        )

    def _drop_on_end(self, event: Any, target_list_id: UUID) -> bool:
        """Append a library Champion or relocate one placed Champion without source gaps."""

        self._reset_drop_target(event)
        source = parse_drag_source_key(getattr(getattr(event, "src", None), "key", None))
        if source is None:
            return False
        if source[0] == "library":
            return self.add_champion_to_list(target_list_id, str(source[1]))

        source_list_id, source_index = self._locate_instance(source[1])
        return self._run_structural(
            "Move Champion",
            lambda: self.editor.move_champion_to_end(
                source_list_id,
                source_index,
                target_list_id,
            ),
        )

    def _drag_will_accept(self, event: Any) -> None:
        ft = flet_module()
        color = ft.Colors.PRIMARY if bool(event.accept) else ft.Colors.ERROR
        event.control.content.border = ft.Border.all(2, color)
        event.control.update()

    def _drag_leave(self, event: Any) -> None:
        self._reset_drop_target(event)

    @staticmethod
    def _reset_drop_target(event: Any) -> None:
        ft = flet_module()
        event.control.content.border = ft.Border.all(1, ft.Colors.OUTLINE_VARIANT)
        event.control.update()

    def _confirm_clear_list(self, list_id: UUID) -> None:
        self._show_confirmation(
            "Clear List?",
            "Remove every Champion from this List?",
            lambda: self.clear_list(list_id),
        )

    def _confirm_delete_list(self, list_id: UUID) -> None:
        self._show_confirmation(
            "Delete List?",
            "Delete this List and all of its placed Champions?",
            lambda: self.delete_list(list_id),
        )

    def _show_confirmation(self, title: str, message: str, action: Callable[[], None]) -> None:
        ft = flet_module()

        def confirm(_event: Any) -> None:
            self._close_dialog()
            action()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(title),
            content=ft.Text(message),
            actions=[
                ft.TextButton(content="Cancel", on_click=event_handler(self._close_dialog)),
                ft.TextButton(content="Confirm", on_click=confirm),
            ],
        )
        self._show_dialog(dialog)

    def _show_dynamic_selection_dialog(
        self,
        list_id: UUID,
        slot_index: int,
        rule: DynamicTraitDefinition,
    ) -> None:
        ft = flet_module()
        champion = self._list(list_id).slots[slot_index].champion
        selected = set(champion.trait_selection.trait_ids)
        choice_controls: dict[str, Any] = {}
        status = ft.Text(size=12)
        apply_button = ft.Button(content="Apply")

        def current_selection() -> TraitSelection:
            return TraitSelection(
                tuple(trait_id for trait_id in rule.choices if trait_id in selected)
            )

        def refresh_validation() -> None:
            issue = validate_dynamic_selection(rule, current_selection())
            status.value = "Selection valid" if issue is None else issue.message
            status.color = ft.Colors.ON_SURFACE_VARIANT if issue is None else ft.Colors.ERROR
            apply_button.disabled = issue is not None
            self.page.update()

        def choose(trait_id: str, event: Any) -> None:
            checked = bool(event.control.value)
            if checked and rule.selection_rule in {
                DynamicSelectionRule.EXACTLY_ONE,
                DynamicSelectionRule.ZERO_OR_ONE,
            }:
                selected.clear()
                selected.add(trait_id)
                for choice_id, control in choice_controls.items():
                    control.value = choice_id == trait_id
            elif checked:
                selected.add(trait_id)
            else:
                selected.discard(trait_id)
            refresh_validation()

        def choice_handler(trait_id: str) -> Callable[[Any], None]:
            def handle(event: Any) -> None:
                choose(trait_id, event)

            return handle

        def apply(_event: Any) -> None:
            selection = current_selection()
            if validate_dynamic_selection(rule, selection) is not None:
                refresh_validation()
                return

            def save_selection() -> None:
                if rule.selection_scope is DynamicSelectionScope.PER_CHAMPION:
                    self.editor.set_champion_trait_selection(
                        list_id,
                        champion.champion_id,
                        selection,
                    )
                else:
                    self.editor.set_trait_selection(list_id, slot_index, selection)

            self._run_structural("Set dynamic Traits", save_selection)
            self._close_dialog()

        choices: list[Any] = []
        for trait_id in rule.choices:
            definition = self._traits_by_id[trait_id]
            checkbox = ft.Checkbox(
                key=f"dynamic-choice-{champion.instance_id}-{trait_id}",
                label=localized_text(self.loaded_set, definition.name_key),
                value=trait_id in selected,
                on_change=choice_handler(trait_id),
            )
            choice_controls[trait_id] = checkbox
            choices.append(checkbox)

        apply_button.key = f"dynamic-apply-{champion.instance_id}"
        apply_button.on_click = apply
        cancel = ft.TextButton(
            key=f"dynamic-cancel-{champion.instance_id}",
            content="Cancel",
            on_click=event_handler(self._close_dialog),
        )
        name = localized_text(
            self.loaded_set,
            self._champions_by_id[champion.champion_id].name_key,
        )
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Dynamic Traits - {name}"),
            content=ft.Column(
                tight=True,
                controls=[ft.Text(dynamic_rule_summary(rule)), *choices, status],
            ),
            actions=[cancel, apply_button],
        )
        refresh_validation()
        self._show_dialog(dialog)

    def _show_dialog(self, dialog: Any) -> None:
        if self._open_dialog is not None:
            self.page.pop_dialog()
        self._open_dialog = dialog
        self.page.show_dialog(dialog)

    def _close_dialog(self) -> None:
        if self._open_dialog is None:
            return
        self.page.pop_dialog()
        self._open_dialog = None

    async def _handle_keyboard_event(self, event: Any) -> None:
        key = str(event.key).casefold()
        modifier = bool(event.ctrl or event.meta)
        if key == "escape" and self._open_dialog is not None:
            self._close_dialog()
            return
        if self._open_dialog is not None:
            return
        if modifier and key == "f":
            if self._champion_search_field is not None:
                self._text_input_focused = True
                await self._champion_search_field.focus()
            return
        if self._text_input_focused or not modifier:
            return
        if key == "z" and bool(event.shift):
            self.redo()
        elif key == "z":
            self.undo()
        elif key == "y":
            self.redo()

    @staticmethod
    def _drop_handler(callback: Callable[..., Any], *args: Any) -> Callable[[Any], Any]:
        def handle(event: Any) -> Any:
            return callback(event, *args)

        return handle

    @staticmethod
    def _name_change_handler(callback: Callable[..., Any], *args: Any) -> Callable[[Any], Any]:
        def handle(event: Any) -> Any:
            value = event.control.value
            if not value.strip():
                return None
            return callback(*args, value)

        return handle

    def _name_finish_handler(
        self, callback: Callable[..., Any], *args: Any
    ) -> Callable[[Any], Any]:
        def handle(event: Any) -> Any:
            self._text_input_focused = False
            value = event.control.value
            if not value.strip():
                self._set_status("Name cannot be empty", error=True)
                self.refresh()
                return None
            callback(*args, value)
            self.flush_text()
            return None

        return handle

    def _focus_handler(self, focused: bool) -> Callable[[Any], None]:
        def handle(_event: Any) -> None:
            self._text_input_focused = focused

        return handle

    @staticmethod
    def _bool_handler(callback: Callable[[bool], Any]) -> Callable[[Any], Any]:
        def handle(event: Any) -> Any:
            return callback(bool(event.control.value))

        return handle
