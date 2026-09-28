"""Concrete local Team-library screen and session-scoped navigation state."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from .constants import APP_NAME
from .flet_helpers import event_handler, flet_module, text_value_handler
from .models import Team
from .persistence import TeamRepository
from .set_display import champion_matches_query, localized_text, set_display_name
from .set_loader import LoadedSet
from .team_library import TeamSimilarity, filter_teams_by_name, rank_teams_by_champions


@dataclass(slots=True)
class LibrarySessionState:
    """Transient Library navigation/search state preserved while a Builder is open."""

    team_search_query: str = ""
    champion_search_query: str = ""
    desired_champion_ids: list[str] = field(default_factory=list)
    selected_set_id: str | None = None
    show_deleted: bool = False


class LibraryView:
    """Imperative Flet Team library backed directly by the local repository."""

    def __init__(
        self,
        page: Any,
        loaded_sets: tuple[LoadedSet, ...],
        repository: TeamRepository,
        *,
        on_open: Callable[[UUID], None],
        assets_dir: Path,
        session: LibrarySessionState | None = None,
    ) -> None:
        if not loaded_sets:
            raise ValueError("loaded_sets must contain at least one valid Set")
        if not isinstance(repository, TeamRepository):
            raise TypeError("repository must be a TeamRepository")
        self.page = page
        self.loaded_sets = tuple(sorted(loaded_sets, key=lambda item: item.manifest.set_id))
        self._sets_by_id = {
            loaded_set.manifest.set_id: loaded_set for loaded_set in self.loaded_sets
        }
        self.repository = repository
        self.on_open = on_open
        self.assets_dir = Path(assets_dir).resolve()
        self.session = session or LibrarySessionState()
        if self.session.selected_set_id not in self._sets_by_id:
            self.session.selected_set_id = self.loaded_sets[0].manifest.set_id
        self.recently_deleted_team_id: UUID | None = None
        self._teams_cache: tuple[Team, ...] | None = None
        self._root: Any | None = None

    def mount(self) -> None:
        """Render the library as the only root page control."""

        self.page.title = APP_NAME
        self._root = flet_module().SafeArea(expand=True, content=self._build_layout())
        self.page.add(self._root)

    def refresh(self) -> None:
        if self._root is None:
            return
        self._root.content = self._build_layout()
        self.page.update()

    def set_team_search(self, value: str) -> None:
        self.session.team_search_query = value
        self.refresh()

    def set_champion_search(self, value: str) -> None:
        self.session.champion_search_query = value
        self.refresh()

    def clear_filters(self) -> None:
        if (
            self.session.team_search_query
            or self.session.champion_search_query
            or self.session.desired_champion_ids
        ):
            self.session.team_search_query = ""
            self.session.champion_search_query = ""
            self.session.desired_champion_ids.clear()
            self.refresh()

    def set_selected_set(self, set_id: str) -> None:
        if set_id not in self._sets_by_id:
            raise ValueError(f"unknown Set ID: {set_id}")
        if set_id != self.session.selected_set_id:
            self.session.selected_set_id = set_id
            self.session.desired_champion_ids.clear()
            self.session.champion_search_query = ""
            self.refresh()

    def add_similarity_champion(self, champion_id: str) -> None:
        if champion_id not in self.selected_set.champions_by_id:
            raise ValueError(f"unknown Champion ID for selected Set: {champion_id}")
        self.session.desired_champion_ids.append(champion_id)
        self.refresh()

    def remove_similarity_champion(self, champion_id: str) -> None:
        try:
            self.session.desired_champion_ids.remove(champion_id)
        except ValueError:
            return
        self.refresh()

    def toggle_deleted(self) -> None:
        self.session.show_deleted = not self.session.show_deleted
        self.refresh()

    def create_team(self) -> None:
        team = Team.create(set_id=self.session.selected_set_id, name="Untitled Team")
        self.repository.save(team)
        self.on_open(team.team_id)

    def open_team(self, team_id: UUID) -> None:
        self.on_open(team_id)

    def soft_delete(self, team_id: UUID) -> None:
        if self.repository.soft_delete(team_id):
            self.recently_deleted_team_id = team_id
            self._reload_teams()
            self.refresh()

    def restore(self, team_id: UUID) -> None:
        if self.repository.restore(team_id):
            if self.recently_deleted_team_id == team_id:
                self.recently_deleted_team_id = None
            self._reload_teams()
            self.refresh()

    def restore_recent(self) -> None:
        team_id = self.recently_deleted_team_id
        if team_id is not None:
            self.restore(team_id)

    def confirm_permanent_delete(self, team_id: UUID) -> None:
        ft = flet_module()
        dialog = ft.AlertDialog(
            title=ft.Text("Permanently delete Team?"),
            content=ft.Text(
                "This removes the Team and all of its Lists permanently. This cannot be undone."
            ),
            actions=[
                ft.TextButton(content="Cancel", on_click=event_handler(self.page.pop_dialog)),
                ft.TextButton(
                    content="Delete permanently",
                    on_click=event_handler(self._delete_permanently, team_id),
                ),
            ],
        )
        self.page.show_dialog(dialog)

    def _delete_permanently(self, team_id: UUID) -> None:
        self.repository.delete_permanently(team_id)
        if self.recently_deleted_team_id == team_id:
            self.recently_deleted_team_id = None
        self._reload_teams()
        self.page.pop_dialog()
        self.refresh()

    @property
    def selected_set(self) -> LoadedSet:
        return self._sets_by_id[self.session.selected_set_id]

    def _reload_teams(self) -> None:
        """Refresh the in-memory Library snapshot after a repository mutation."""

        self._teams_cache = self.repository.load_all(include_deleted=True)

    def _library_teams(self) -> tuple[Team, ...]:
        # A LibraryView owns no long-lived editor. Its repository state changes only through
        # the mutation methods above, which reload this cache explicitly. Search/filter UI
        # can therefore rerender without re-reading every aggregate on each keystroke.
        if self._teams_cache is None:
            self._reload_teams()
        if self.session.show_deleted:
            return tuple(team for team in self._teams_cache if team.deleted_at is not None)
        return tuple(team for team in self._teams_cache if team.deleted_at is None)

    def _visible_ranked_teams(self) -> tuple[TeamSimilarity, ...]:
        teams = filter_teams_by_name(self._library_teams(), self.session.team_search_query)
        if self.session.desired_champion_ids:
            teams = tuple(team for team in teams if team.set_id == self.session.selected_set_id)
        return rank_teams_by_champions(teams, tuple(self.session.desired_champion_ids))

    def _build_layout(self) -> Any:
        ft = flet_module()
        return ft.Column(
            expand=True,
            controls=[
                self._build_header(ft),
                ft.Divider(height=1),
                ft.Row(
                    expand=True,
                    vertical_alignment=ft.CrossAxisAlignment.STRETCH,
                    controls=[
                        ft.Container(expand=True, padding=16, content=self._build_team_list(ft)),
                        ft.VerticalDivider(width=1),
                        ft.Container(
                            width=320, padding=16, content=self._build_similarity_panel(ft)
                        ),
                    ],
                ),
            ],
        )

    def _build_header(self, ft: Any) -> Any:
        set_button = ft.PopupMenuButton(
            key="library-set-selector",
            tooltip="Set for new Teams and similarity search",
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.LAYERS),
                    ft.Text(set_display_name(self.selected_set)),
                    ft.Icon(ft.Icons.ARROW_DROP_DOWN),
                ]
            ),
            items=[
                ft.PopupMenuItem(
                    content=set_display_name(loaded_set),
                    on_click=event_handler(self.set_selected_set, loaded_set.manifest.set_id),
                )
                for loaded_set in self.loaded_sets
            ],
        )
        return ft.Container(
            padding=12,
            content=ft.Row(
                controls=[
                    ft.Text("Team Library", size=26, weight=ft.FontWeight.BOLD),
                    ft.TextField(
                        key="library-team-search",
                        hint_text="Search Teams",
                        value=self.session.team_search_query,
                        expand=True,
                        on_change=text_value_handler(self.set_team_search),
                    ),
                    set_button,
                    ft.Button(
                        key="library-create-team",
                        content="New Team",
                        icon=ft.Icons.ADD,
                        on_click=event_handler(self.create_team),
                    ),
                    ft.Button(
                        key="library-toggle-trash",
                        content="Teams" if self.session.show_deleted else "Trash",
                        icon=ft.Icons.INBOX
                        if self.session.show_deleted
                        else ft.Icons.DELETE_OUTLINE,
                        on_click=event_handler(self.toggle_deleted),
                    ),
                ]
            ),
        )

    def _build_team_list(self, ft: Any) -> Any:
        ranked = self._visible_ranked_teams()
        controls: list[Any] = []
        if self.recently_deleted_team_id is not None and not self.session.show_deleted:
            controls.append(
                ft.Container(
                    key="library-delete-undo",
                    padding=8,
                    content=ft.Row(
                        controls=[
                            ft.Text("Team moved to Trash."),
                            ft.TextButton(
                                content="Restore",
                                on_click=event_handler(self.restore_recent),
                            ),
                        ]
                    ),
                )
            )
        if not ranked:
            if self.session.show_deleted:
                empty = self._empty_state(ft, "Trash is empty", "Deleted Teams will appear here.")
            elif self.session.team_search_query or self.session.desired_champion_ids:
                empty = self._empty_state(
                    ft,
                    "No Teams match",
                    "Clear the current search and Champion filters to see the full library.",
                    action=ft.Button(
                        key="library-clear-filters-empty",
                        content="Clear filters",
                        on_click=event_handler(self.clear_filters),
                    ),
                )
            else:
                empty = self._empty_state(
                    ft,
                    "No Teams yet",
                    "Create your first Team to start planning Lists.",
                    action=ft.Button(
                        key="library-create-empty",
                        content="Create Team",
                        icon=ft.Icons.ADD,
                        on_click=event_handler(self.create_team),
                    ),
                )
            controls.append(empty)
        else:
            controls.extend(self._build_team_card(ft, result) for result in ranked)
        return ft.ListView(expand=True, spacing=10, controls=controls)

    def _build_team_card(self, ft: Any, result: TeamSimilarity) -> Any:
        team = result.team
        loaded_set = self._sets_by_id.get(team.set_id)
        missing_set = loaded_set is None
        if self.session.desired_champion_ids:
            preview = next(
                team_list for team_list in team.lists if team_list.list_id == result.best_list_id
            )
            preview_label = "Best match"
        else:
            preview = team.primary_list
            preview_label = "Primary"
        preview_ids = [
            slot.champion.champion_id for slot in preview.slots if slot.champion is not None
        ]
        if loaded_set is None:
            preview_names = preview_ids
        else:
            champions_by_id = loaded_set.champions_by_id
            preview_names = [
                localized_text(loaded_set, champions_by_id[champion_id].name_key)
                if champion_id in champions_by_id
                else champion_id
                for champion_id in preview_ids
            ]
        preview_text = ", ".join(preview_names[:8]) if preview_names else "No Champions yet"
        similarity_text = ""
        if self.session.desired_champion_ids:
            similarity_text = (
                f"Best List: {result.matches}/{len(self.session.desired_champion_ids)} matches"
            )
        actions: list[Any] = []
        if self.session.show_deleted:
            actions.extend(
                [
                    ft.Button(
                        key=f"library-restore-{team.team_id}",
                        content="Restore",
                        icon=ft.Icons.RESTORE,
                        on_click=event_handler(self.restore, team.team_id),
                    ),
                    ft.PopupMenuButton(
                        key=f"library-deleted-menu-{team.team_id}",
                        icon=ft.Icons.MORE_VERT,
                        items=[
                            ft.PopupMenuItem(
                                content="Delete permanently",
                                on_click=event_handler(self.confirm_permanent_delete, team.team_id),
                            )
                        ],
                    ),
                ]
            )
        else:
            actions.extend(
                [
                    ft.Button(
                        key=f"library-open-{team.team_id}",
                        content="Open",
                        icon=ft.Icons.OPEN_IN_NEW,
                        disabled=missing_set,
                        on_click=event_handler(self.open_team, team.team_id),
                    ),
                    ft.IconButton(
                        key=f"library-delete-{team.team_id}",
                        icon=ft.Icons.DELETE_OUTLINE,
                        tooltip="Move Team to Trash",
                        on_click=event_handler(self.soft_delete, team.team_id),
                    ),
                ]
            )
        set_name = team.set_id if loaded_set is None else set_display_name(loaded_set)
        details = [
            ft.Text(team.name, size=18, weight=ft.FontWeight.BOLD),
            ft.Text(f"Set: {set_name} | Lists: {len(team.lists)}"),
            ft.Text(f"{preview_label}: {preview.name} | {preview_text}"),
            ft.Text(_format_updated(team.updated_at)),
        ]
        if similarity_text:
            details.append(ft.Text(similarity_text))
        if missing_set:
            details.append(ft.Text("Required Set is not available.", color=ft.Colors.ERROR))
        return ft.Container(
            key=f"library-team-{team.team_id}",
            padding=12,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=10,
            content=ft.Row(
                controls=[ft.Column(expand=True, controls=details), ft.Row(controls=actions)]
            ),
        )

    def _build_similarity_panel(self, ft: Any) -> Any:
        counts = Counter(self.session.desired_champion_ids)
        chips = [
            ft.Button(
                key=f"library-selected-{champion_id}",
                content=(
                    localized_text(
                        self.selected_set,
                        self.selected_set.champions_by_id[champion_id].name_key,
                    )
                    + (f" x{count}" if count > 1 else "")
                ),
                icon=ft.Icons.CLOSE,
                on_click=event_handler(self.remove_similarity_champion, champion_id),
            )
            for champion_id, count in counts.items()
        ]
        matches = [
            champion
            for champion in self.selected_set.champions
            if champion_matches_query(
                self.selected_set, champion, self.session.champion_search_query
            )
        ]
        champion_controls = [
            ft.Button(
                key=f"library-similarity-add-{champion.id}",
                content=localized_text(self.selected_set, champion.name_key),
                icon=ft.Icons.ADD,
                on_click=event_handler(self.add_similarity_champion, champion.id),
            )
            for champion in matches[:20]
        ]
        if len(matches) > 20:
            champion_controls.append(
                ft.Text(
                    "Showing the first 20 matches. Search to narrow the list.",
                    key="library-similarity-limit-note",
                )
            )
        return ft.Column(
            expand=True,
            controls=[
                ft.Text("Find similar Teams", size=20, weight=ft.FontWeight.BOLD),
                ft.Text("Select Champions; duplicates count."),
                ft.Row(controls=chips, wrap=True, spacing=6, run_spacing=6)
                if chips
                else ft.Text("No Champions selected."),
                ft.TextField(
                    key="library-champion-search",
                    hint_text="Search Champions or Traits",
                    value=self.session.champion_search_query,
                    on_change=text_value_handler(self.set_champion_search),
                ),
                ft.ListView(expand=True, spacing=6, controls=champion_controls),
                ft.Button(
                    key="library-clear-filters",
                    content="Clear filters",
                    icon=ft.Icons.CLEAR_ALL,
                    disabled=not (
                        self.session.team_search_query
                        or self.session.champion_search_query
                        or self.session.desired_champion_ids
                    ),
                    on_click=event_handler(self.clear_filters),
                ),
            ],
        )

    @staticmethod
    def _empty_state(ft: Any, title: str, message: str, *, action: Any | None = None) -> Any:
        controls = [
            ft.Icon(ft.Icons.INBOX_OUTLINED, size=36),
            ft.Text(title, size=20, weight=ft.FontWeight.BOLD),
            ft.Text(message),
        ]
        if action is not None:
            controls.append(action)
        return ft.Container(
            key="library-empty-state",
            alignment=ft.Alignment.CENTER,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=controls,
            ),
        )


def _format_updated(value: datetime) -> str:
    return f"Updated {value.astimezone().strftime('%Y-%m-%d %H:%M')}"
