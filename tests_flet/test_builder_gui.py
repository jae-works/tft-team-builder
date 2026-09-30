"""Packaged-app smoke flow across the real Team Library and Builder screens."""

from __future__ import annotations

import asyncio

import flet.testing as ftt


async def _wait_for_text(
    tester: ftt.Tester, text: str, *, attempts: int = 240, delay_seconds: float = 0.25
):
    """Wait for visible packaged-app readiness without depending on Flet 1.0.1 keys."""

    for _ in range(attempts):
        finder = await tester.find_by_text(text)
        if finder.count:
            return finder
        await asyncio.sleep(delay_seconds)
        # Startup can show an indeterminate progress animation. Pump one frame
        # instead of waiting for every scheduled animation to settle.
        await tester.pump()
    return await tester.find_by_text(text)


async def _wait_for_library_or_error(
    tester: ftt.Tester, *, attempts: int = 240, delay_seconds: float = 0.25
):
    """Stop polling when the Library or either application error surface is visible."""

    for _ in range(attempts):
        library = await tester.find_by_text("Team Library")
        startup_error = await tester.find_by_key("app-startup-error")
        flet_error = await tester.find_by_text("Error running app")
        if library.count or startup_error.count or flet_error.count:
            return library, startup_error, flet_error
        await asyncio.sleep(delay_seconds)
        await tester.pump()
    return (
        await tester.find_by_text("Team Library"),
        await tester.find_by_key("app-startup-error"),
        await tester.find_by_text("Error running app"),
    )


async def test_library_builder_core_flow(flet_app: ftt.FletTestApp) -> None:
    """Exercise packaged startup, navigation, one List mutation and persistence flow."""

    tester = flet_app.tester
    await tester.pump()

    library, startup_error, flet_error = await _wait_for_library_or_error(tester)
    assert startup_error.count == 0
    assert flet_error.count == 0
    assert library.count == 1
    assert (await tester.find_by_text("New Team")).count == 1

    # Python-side control keys were intermittently unavailable through Flet 1.0.1's
    # packaged tester even when the visible control existed. This smoke deliberately
    # follows user-visible text/tooltips; key behavior remains covered by unit tests.
    await tester.tap(await tester.find_by_text("New Team"))
    await tester.pump_and_settle()
    assert (await _wait_for_text(tester, "Champion Library")).count == 1
    assert (await tester.find_by_text("Traits")).count == 1

    add_buttons = await tester.find_by_tooltip("Add to active List")
    assert add_buttons.count >= 1
    await tester.tap(add_buttons.first)
    await tester.pump_and_settle()
    remove_buttons = await tester.find_by_tooltip("Remove Champion")
    assert remove_buttons.count >= 1
    assert (await tester.find_by_text("Add unit")).count == 1

    await tester.tap(remove_buttons.first)
    await tester.pump_and_settle()
    assert (await tester.find_by_text("Add unit")).count == 1

    await tester.tap(await tester.find_by_tooltip("Back to Team Library"))
    await tester.pump_and_settle()
    assert (await _wait_for_text(tester, "Team Library")).count == 1
    assert (await tester.find_by_text("Untitled Team")).count >= 1

    delete_buttons = await tester.find_by_tooltip("Move Team to Trash")
    assert delete_buttons.count >= 1
    await tester.tap(delete_buttons.first)
    await tester.pump_and_settle()
    assert (await tester.find_by_text("Team moved to Trash.")).count == 1

    await tester.tap(await tester.find_by_text("Trash"))
    await tester.pump_and_settle()
    restore = await tester.find_by_text("Restore")
    assert restore.count >= 1
    await tester.tap(restore.first)
    await tester.pump_and_settle()

    await tester.tap(await tester.find_by_text("Teams"))
    await tester.pump_and_settle()
    assert (await _wait_for_text(tester, "Team Library")).count == 1
