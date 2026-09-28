from __future__ import annotations

import json
import tomllib
from pathlib import Path


def test_project_manifest_is_valid_json(project_root: Path) -> None:
    payload = json.loads((project_root / "PROJECT_MANIFEST.json").read_text(encoding="utf-8"))
    assert payload["project"] == "TFT Team Builder"
    with (project_root / "pyproject.toml").open("rb") as handle:
        project_version = tomllib.load(handle)["project"]["version"]
    assert payload["version"] == project_version
    assert (
        payload["current_state"]
        == "block_7_corrected_pipeline_pending_live_set_18_generation_and_windows_gate"
    )
    assert payload["current_block"] == 7
    assert payload["next_block"] == 7


def test_release_documents_match_package_version(project_root: Path) -> None:
    with (project_root / "pyproject.toml").open("rb") as handle:
        version = tomllib.load(handle)["project"]["version"]

    expected_fragments = {
        "README.md": f"Current version: {version}",
        "PROGRESS.md": f"Current version: {version}",
        "PROJECT_CONTEXT.md": f"Current version: {version}",
        "LICENSE_REVIEW.md": f"Project version: {version}",
        "BLOCK_06_REPORT.md": f"Version: {version}",
    }
    for relative, expected in expected_fragments.items():
        text = (project_root / relative).read_text(encoding="ascii")
        assert expected in text, relative


def test_manifest_includes_current_block_plans_and_report(project_root: Path) -> None:
    payload = json.loads((project_root / "PROJECT_MANIFEST.json").read_text(encoding="ascii"))
    for filename in (
        "BLOCK_03_PLAN.md",
        "BLOCK_03_REPORT.md",
        "BLOCK_04_PLAN.md",
        "BLOCK_04_REPORT.md",
        "BLOCK_05_PLAN.md",
        "BLOCK_05_REPORT.md",
        "BLOCK_06_PLAN.md",
        "BLOCK_06_REPORT.md",
        "BLOCK_07_PLAN.md",
    ):
        assert filename in payload["required_project_documents"]
        assert filename in payload["mirrored_project_documents"]


def test_every_manifest_required_document_exists(project_root: Path) -> None:
    payload = json.loads((project_root / "PROJECT_MANIFEST.json").read_text(encoding="utf-8"))
    required = payload["required_project_documents"]
    assert required
    missing = [relative for relative in required if not (project_root / relative).is_file()]
    assert missing == []


def test_project_docs_contains_exact_mirrors_of_core_documents(project_root: Path) -> None:
    payload = json.loads((project_root / "PROJECT_MANIFEST.json").read_text(encoding="ascii"))
    mirror_root = project_root / "project_docs"
    for filename in payload["mirrored_project_documents"]:
        source = project_root / filename
        mirror = mirror_root / filename
        assert source.is_file(), filename
        assert mirror.is_file(), filename
        assert mirror.read_bytes() == source.read_bytes(), filename


def test_manifest_records_required_engineering_language_policy(project_root: Path) -> None:
    payload = json.loads((project_root / "PROJECT_MANIFEST.json").read_text(encoding="utf-8"))
    engineering = payload["engineering_rules"]
    assert engineering["code_language"] == "English"
    assert engineering["documentation_language"] == "English"
    assert engineering["project_authored_technical_text_ascii_safe"] is True
    assert engineering["project_owned_paths_ascii_only"] is True


def test_manifest_records_current_verification(project_root: Path) -> None:
    payload = json.loads((project_root / "PROJECT_MANIFEST.json").read_text(encoding="utf-8"))
    verification = payload["verification"]
    assert verification["pytest_passed"] == 652
    assert verification["statement_coverage_percent"] == 100.0
    assert verification["branch_coverage_percent"] == 100.0
    assert verification["production_statements"] == 2736
    assert verification["production_branches"] == 810
    assert verification["compileall_passed"] is True
    assert verification["ascii_policy_passed"] is True
    assert verification["sample_set_regenerated"] is True
    assert verification["sample_set_validated"] is True
    assert verification["block_2_persistence_roundtrip_verified"] is True
    assert verification["block_2_migration_verified"] is True
    assert verification["block_2_backup_restore_verified"] is True
    assert verification["block_3_editor_verified"] is True
    assert verification["block_3_trait_engine_verified"] is True
    assert verification["block_3_undo_redo_verified"] is True
    assert verification["block_3_builder_smoke_passed"] is True
    assert verification["windows_0_2_2_ruff_sim300_errors"] == 1
    assert verification["windows_0_3_0_pytest_passed"] == 529
    assert verification["windows_0_3_0_coverage_percent"] == 100.0
    assert verification["windows_0_3_0_ruff_lint_passed"] is False
    assert verification["windows_0_3_0_ruff_format_applied_files"] == 4
    assert verification["windows_0_3_0_ruff_pth201_errors"] == 1
    assert verification["windows_0_3_0_ruff_ruf043_errors"] == 1
    assert verification["windows_0_3_0_builder_smoke_passed"] is True
    assert verification["block_3_ruff_findings_corrected"] is True
    assert verification["block_3_semantic_regression_tests_expanded"] is True
    assert verification["block_3_editor_autosave_integration_verified"] is True
    assert verification["block_4_plan_prepared"] is True
    assert verification["flet_integration_test_config_prepared"] is True
    assert verification["block_3_redundant_validation_removed"] is True
    assert verification["block_3_redundant_trait_lookup_removed"] is True
    assert verification["block_3_editor_stress_operations"] == 30000
    assert verification["block_3_trait_oracle_generated_lists"] == 2500
    assert verification["production_duplicate_function_groups"] == 0
    assert verification["all_python_duplicate_function_groups"] == 0
    assert verification["static_python_files_audited"] == 62
    assert verification["windows_0_3_1_pytest_passed"] == 537
    assert verification["windows_0_3_1_ruff_lint_passed"] is True
    assert verification["windows_0_3_1_ruff_format_final_passed"] is True
    assert verification["block_4_gui_implemented"] is True
    assert verification["block_4_flet_integration_suite_added"] is True
    assert (
        verification["block_4_exact_flet_integration_verified_in_implementation_sandbox"] is False
    )
    assert verification["windows_0_4_0_pytest_passed"] == 561
    assert verification["windows_0_4_0_ruff_format_initial_drift_files"] == 5
    assert verification["windows_0_4_0_ruff_i001_errors"] == 1
    assert verification["windows_0_4_0_flet_integration_blocked_by_developer_mode"] is True
    assert verification["windows_0_4_0_flet_integration_coverage_configuration_conflict"] is True
    assert verification["block_4_dense_slot_presentation_verified"] is True
    assert verification["block_4_fixed_width_save_indicator_verified"] is True
    assert verification["block_4_transient_blank_name_edit_handled"] is True
    assert verification["block_5_plan_prepared"] is True
    assert verification["block_4_1_local_pytest_passed"] == 564
    assert verification["block_4_1_local_coverage_percent"] == 100.0
    assert verification["block_4_1_local_smokes_passed"] is True
    assert verification["block_4_1_static_audit_passed"] is True
    assert verification["block_4_1_exact_ruff_windows_pending"] is False
    assert verification["block_4_1_flet_integration_windows_pending"] is True

    assert verification["windows_0_4_1_pytest_passed"] == 564
    assert verification["windows_0_4_1_ruff_format_initial_drift_files"] == 2
    assert verification["windows_0_4_1_ruff_format_final_passed"] is True
    assert verification["windows_0_4_1_ruff_lint_passed"] is True
    assert verification["windows_0_4_1_flet_cli_separator_rejected"] is True
    assert verification["block_5_remove_geometry_regression_fixed"] is True
    assert verification["block_5_search_verified"] is True
    assert verification["block_5_drag_translation_verified"] is True
    assert verification["block_5_dynamic_trait_editor_verified"] is True
    assert verification["block_5_keyboard_shortcuts_verified"] is True
    assert verification["block_5_local_pytest_passed"] == 585
    assert verification["windows_0_5_0_pytest_passed"] == 585
    assert verification["windows_0_5_0_coverage_percent"] == 100.0
    assert verification["windows_0_5_0_ruff_format_initial_drift_files"] == 3
    assert verification["windows_0_5_0_ruff_format_final_passed"] is True
    assert verification["windows_0_5_0_ruff_lint_passed"] is False
    assert verification["windows_0_5_0_ruff_e731_errors"] == 2
    assert verification["windows_0_5_0_flet_test_host_provisioned"] is True
    assert verification["windows_0_5_0_flet_flutter_process_exit_code"] == 0
    assert verification["windows_0_5_0_flet_builder_key_found"] is False
    assert verification["windows_0_5_0_normal_flet_run_passed"] is True
    assert verification["block_5_1_packaged_entrypoint_corrected"] is True
    assert verification["block_5_1_packaged_entrypoint_regression_tested"] is True
    assert verification["block_5_1_ruff_e731_corrected"] is True
    assert verification["block_5_1_redundant_catalog_helper_removed"] is True
    assert verification["block_5_1_set_lookup_maps_cached"] is True
    assert verification["block_5_1_source_slot_validation_consolidated"] is True
    assert verification["block_5_1_flet_probe_socket_shim"] is True
    assert verification["block_5_1_editor_stress_operations"] == 750
    assert verification["block_5_1_local_pytest_passed"] == 586
    assert verification["block_5_1_local_coverage_percent"] == 100.0
    assert verification["block_5_1_exact_ruff_windows_pending"] is False
    assert verification["block_5_1_packaged_flet_windows_pending"] is True
    assert verification["block_5_exact_ruff_windows_pending"] is False
    assert verification["block_5_packaged_flet_windows_pending"] is True
    assert verification["block_6_plan_prepared"] is True
    assert verification["block_6_hci_plan_refined"] is True
    assert verification["windows_0_5_1_pytest_passed"] == 586
    assert verification["windows_0_5_1_coverage_percent"] == 100.0
    assert verification["windows_0_5_1_ruff_format_initial_drift_files"] == 2
    assert verification["windows_0_5_1_ruff_format_final_passed"] is True
    assert verification["windows_0_5_1_ruff_lint_passed"] is True
    assert verification["windows_0_5_1_flet_test_host_provisioned"] is True
    assert verification["windows_0_5_1_flet_flutter_process_exit_code"] == 0
    assert verification["windows_0_5_1_flet_stable_app_key_found"] is False
    assert verification["windows_0_5_1_normal_flet_run_passed"] is True
    assert verification["windows_0_5_1_stream_writer_warning_observed"] is True
    assert verification["block_6_team_library_implemented"] is True
    assert verification["block_6_similarity_engine_verified"] is True
    assert verification["block_6_soft_delete_restore_verified"] is True
    assert verification["block_6_navigation_state_verified"] is True
    assert verification["block_6_hci_empty_states_verified"] is True
    assert verification["block_6_last_team_restore_regression_verified"] is True
    assert verification["block_6_packaged_flet_smoke_updated"] is True
    assert verification["block_6_exact_windows_pending"] is True
    assert verification["block_7_plan_prepared"] is True
    assert verification["block_6_local_pytest_passed"] == 617
    assert verification["block_6_local_statement_coverage_percent"] == 100.0
    assert verification["block_6_local_branch_coverage_percent"] == 100.0
    assert verification["block_6_local_smokes_passed"] is True
    assert verification["block_6_static_audit_passed"] is True
    assert verification["block_6_1_batched_library_load_verified"] is True
    assert verification["block_6_1_library_snapshot_cache_verified"] is True
    assert verification["block_6_1_similarity_preview_verified"] is True
    assert verification["block_6_1_shared_flet_helpers_verified"] is True
    assert verification["block_6_1_hci_requirements_refined"] is True
    assert verification["block_6_1_local_pytest_passed"] == 623
    assert verification["block_6_1_local_statement_coverage_percent"] == 100.0
    assert verification["block_6_1_local_branch_coverage_percent"] == 100.0
    assert verification["block_6_1_exact_windows_pending"] is True
    assert verification["windows_0_6_1_pytest_passed"] == 623
    assert verification["windows_0_6_1_coverage_percent"] == 100.0
    assert verification["windows_0_6_1_ruff_format_initial_drift_files"] == 9
    assert verification["windows_0_6_1_ruff_format_final_passed"] is True
    assert verification["windows_0_6_1_ruff_lint_passed"] is False
    assert verification["windows_0_6_1_ruff_f401_errors"] == 3
    assert verification["windows_0_6_1_git_diff_check_passed"] is False
    assert verification["windows_0_6_1_flet_test_host_provisioned"] is True
    assert verification["windows_0_6_1_flet_flutter_process_exit_code"] == 79
    assert verification["windows_0_6_1_flet_integration_passed"] is False
    assert verification["windows_0_6_1_stream_writer_warning_observed"] is True
    assert verification["windows_0_6_1_normal_flet_run_passed"] is True
    assert verification["block_6_2_reported_ruff_findings_corrected"] is True
    assert verification["block_6_2_startup_set_validation_single_pass"] is True
    assert verification["block_6_2_loaded_set_lookup_maps_cached"] is True
    assert verification["block_6_2_library_localized_set_names"] is True
    assert verification["block_6_2_similarity_wrap_and_cap_hint"] is True
    assert verification["block_6_2_flet_remote_writer_cleanup_shim"] is True
    assert verification["block_6_2_hidden_quality_workflow_restored"] is True
    assert verification["block_6_2_local_pytest_passed"] == 627
    assert verification["block_6_2_local_statement_coverage_percent"] == 100.0
    assert verification["block_6_2_local_branch_coverage_percent"] == 100.0
    assert verification["block_6_2_exact_windows_pending"] is True


def test_manifest_records_deferred_cross_platform_direction(project_root: Path) -> None:
    payload = json.loads((project_root / "PROJECT_MANIFEST.json").read_text(encoding="utf-8"))
    platform = payload["platform_strategy"]
    assert platform["required_first_target"] == "Windows desktop"
    assert platform["browser"] == "deferred possible target"
    assert platform["mobile_tablet"] == "deferred possible target"
    assert platform["core_must_remain_ui_independent"] is True


def test_license_review_is_required_before_public_release(project_root: Path) -> None:
    payload = json.loads((project_root / "PROJECT_MANIFEST.json").read_text(encoding="utf-8"))
    assert payload["engineering_rules"]["public_release_license_audit_required"] is True
    license_review = (project_root / "LICENSE_REVIEW.md").read_text(encoding="ascii")
    assert "Public binary release gate" in license_review
    assert "Riot/TFT data and assets" in license_review
