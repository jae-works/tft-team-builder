"""Packaged-app smoke flows for the real Block 5 Flet screen."""

from __future__ import annotations

import flet.testing as ftt


async def test_builder_gui_core_flow(flet_app: ftt.FletTestApp) -> None:
    tester = flet_app.tester
    await tester.pump_and_settle()

    assert (await tester.find_by_key("builder-startup-error")).count == 0
    assert (await tester.find_by_key("builder-team-name")).count == 1
    assert (await tester.find_by_key("builder-new-list")).count == 1
    assert (await tester.find_by_key("builder-champion-search")).count == 1
    assert (await tester.find_by_key("builder-save-status")).count == 1

    await tester.tap(await tester.find_by_key("champion-add-sample_guardian"))
    await tester.pump_and_settle()
    assert (await tester.find_by_key("trait-sample_guard")).count == 1
    assert (await tester.find_by_tooltip("Remove Champion")).count == 1
    assert (await tester.find_by_text("Add unit")).count == 1

    # Regression for the clipped/missing Guardian remove action reported after Block 4.1.
    await tester.tap(await tester.find_by_tooltip("Remove Champion"))
    await tester.pump_and_settle()
    assert (await tester.find_by_tooltip("Remove Champion")).count == 0
    assert (await tester.find_by_text("Add unit")).count == 1

    search = await tester.find_by_key("builder-champion-search")
    await tester.enter_text(search, "arcane")
    await tester.pump_and_settle()
    assert (await tester.find_by_key("champion-sample_guardian")).count == 0
    assert (await tester.find_by_key("champion-sample_mage")).count == 1
    assert (await tester.find_by_key("champion-sample_flex")).count == 1

    await tester.tap(await tester.find_by_key("champion-add-sample_flex"))
    await tester.pump_and_settle()
    assert (await tester.find_by_key("builder-dynamic-issues")).count == 1
    assert (await tester.find_by_key("builder-fix-dynamic")).count == 1

    await tester.tap(await tester.find_by_key("builder-fix-dynamic"))
    await tester.pump_and_settle()
    choice = await tester.find_by_text("Sample Arcane")
    await tester.tap(choice.last)
    await tester.pump_and_settle()
    apply_button = await tester.find_by_text("Apply")
    await tester.tap(apply_button.last)
    await tester.pump_and_settle()
    assert (await tester.find_by_key("builder-dynamic-issues")).count == 0

    assert (await tester.find_by_text("Open")).count == 0
    await tester.tap(await tester.find_by_key("builder-new-list"))
    await tester.pump_and_settle()
    assert (await tester.find_by_text("Open")).count == 1

    await tester.tap(await tester.find_by_key("builder-undo"))
    await tester.pump_and_settle()
    assert (await tester.find_by_text("Open")).count == 0

    await tester.tap(await tester.find_by_key("builder-redo"))
    await tester.pump_and_settle()
    assert (await tester.find_by_text("Open")).count == 1
