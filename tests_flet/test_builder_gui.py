"""Packaged-app smoke flow across the real Team Library and Builder screens."""

from __future__ import annotations

import asyncio

import flet.testing as ftt


async def _wait_for_key(
    tester: ftt.Tester, key: str, *, attempts: int = 120, delay_seconds: float = 0.25
):
    """Wait for embedded Python startup without hiding a permanently missing control."""

    for _ in range(attempts):
        finder = await tester.find_by_key(key)
        if finder.count:
            return finder
        await asyncio.sleep(delay_seconds)
        # Startup can show an indeterminate progress animation. Pump one frame
        # instead of waiting for every scheduled animation to settle.
        await tester.pump()
    return await tester.find_by_key(key)


async def _wait_for_library_or_error(
    tester: ftt.Tester, *, attempts: int = 120, delay_seconds: float = 0.25
):
    """Stop startup polling as soon as either the Library or blocking error is visible."""

    for _ in range(attempts):
        library = await tester.find_by_key("library-team-search")
        error = await tester.find_by_key("app-startup-error")
        if library.count or error.count:
            return library, error
        await asyncio.sleep(delay_seconds)
        # Startup can show an indeterminate progress animation. Pump one frame
        # instead of waiting for every scheduled animation to settle.
        await tester.pump()
    return await tester.find_by_key("library-team-search"), await tester.find_by_key(
        "app-startup-error"
    )


async def test_library_builder_core_flow(flet_app: ftt.FletTestApp) -> None:
    tester = flet_app.tester
    await tester.pump()

    library_search, startup_error = await _wait_for_library_or_error(tester)
    assert startup_error.count == 0
    assert library_search.count == 1
    assert (await tester.find_by_key("library-create-team")).count == 1

    await tester.tap(await tester.find_by_key("library-create-team"))
    await tester.pump_and_settle()
    builder_name = await _wait_for_key(tester, "builder-team-name")
    assert builder_name.count == 1
    assert (await tester.find_by_key("builder-back")).count == 1

    await tester.tap(await tester.find_by_key("champion-add-sample_guardian"))
    await tester.pump_and_settle()
    assert (await tester.find_by_tooltip("Remove Champion")).count >= 1
    assert (await tester.find_by_text("Add unit")).count == 1

    await tester.tap((await tester.find_by_tooltip("Remove Champion")).first)
    await tester.pump_and_settle()
    assert (await tester.find_by_text("Add unit")).count == 1

    await tester.enter_text(builder_name, "Packaged Smoke Team")
    await tester.pump_and_settle()
    await tester.tap(await tester.find_by_key("builder-back"))
    await tester.pump_and_settle()
    assert (await _wait_for_key(tester, "library-team-search")).count == 1

    await tester.enter_text(await tester.find_by_key("library-team-search"), "Packaged Smoke Team")
    await tester.pump_and_settle()
    assert (await tester.find_by_text("Packaged Smoke Team")).count >= 1

    delete_buttons = await tester.find_by_tooltip("Move Team to Trash")
    assert delete_buttons.count >= 1
    await tester.tap(delete_buttons.first)
    await tester.pump_and_settle()
    assert (await tester.find_by_key("library-delete-undo")).count == 1

    await tester.tap(await tester.find_by_key("library-toggle-trash"))
    await tester.pump_and_settle()
    restore = await tester.find_by_text("Restore")
    assert restore.count >= 1
    await tester.tap(restore.first)
    await tester.pump_and_settle()

    await tester.tap(await tester.find_by_key("library-toggle-trash"))
    await tester.pump_and_settle()
    assert (await tester.find_by_key("library-team-search")).count == 1
