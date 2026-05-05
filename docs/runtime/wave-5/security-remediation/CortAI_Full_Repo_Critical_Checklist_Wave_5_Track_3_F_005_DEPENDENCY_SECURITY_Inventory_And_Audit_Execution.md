---
artifact_id: cortai_full_repo_critical_checklist_wave_5_track_3_f_005_dependency_security_inventory_and_audit_execution
artifact_name: CortAI Full Repo Critical Checklist Wave 5 Track 3 F-005 DEPENDENCY SECURITY Inventory And Audit Execution
artifact_type: wave_5_track_3_f_005_dependency_security_inventory_and_audit_execution
system: CortAI
date: 2026-05-04
lane: Wave 5 Security Remediation
system_state: SAFE_PRE_CROSSING
hold_status: HOLD_CRITICAL_PRESERVED

execution_mode: controlled_dependency_inventory_and_audit_execution
security_track: F_005_DEPENDENCY_SECURITY
reviewed_authorization: CortAI Full Repo Critical Checklist Wave 5 Track 3 F-005 DEPENDENCY SECURITY Execution Authorization Review
selected_design: audit_first_minimal_safe_upgrade_with_reproducibility_boundary

inventory_execution_completed: true
dependency_audit_execution_completed: true
pip_audit_execution_completed: true
pip_audit_result: completed_with_findings
dependency_change_performed: false
requirements_change_performed: false
lockfile_change_performed: false
package_install_performed: false
package_upgrade_performed: false
test_execution_performed: false
runtime_execution_performed: false

audit_summary:
  vulnerable_packages: 5
  vulnerabilities: 6
  critical_findings_count: not_reported_by_tool_output
  high_findings_count: not_reported_by_tool_output
  medium_findings_count: not_reported_by_tool_output

runtime_integration_authorized: false
runtime_execution_authorized: false
application_external_call_authorized: false
credential_access_authorized: false
production_ready: false
---

# CortAI Full Repo Critical Checklist Wave 5 Track 3 F-005 DEPENDENCY SECURITY Inventory And Audit Execution

## 1. Purpose

This artifact records the controlled execution of the authorized Track 3 dependency inventory and dependency audit.

It records manifest discovery, selected audit scope, `pip-audit` execution, vulnerable package findings, and future remediation candidates.

It does not change dependencies, install packages, upgrade packages, modify lockfiles, run tests, execute runtime, access credentials, authorize application external calls, or declare production readiness.

## 2. Authorization Lineage

```yaml
authorization_lineage:
  execution_authorization_review:
    name: CortAI Full Repo Critical Checklist Wave 5 Track 3 F-005 DEPENDENCY SECURITY Execution Authorization Review
    path: docs/runtime/wave-5/security-remediation/CortAI_Full_Repo_Critical_Checklist_Wave_5_Track_3_F_005_DEPENDENCY_SECURITY_Execution_Authorization_Review.md
    review_verdict: PASS_WITH_MONITORING
    dependency_inventory_authorized_for_future_step: true
    dependency_audit_authorized_for_future_step: true
    pip_audit_execution_authorized_for_future_step: true
    dependency_change_authorized: false
    package_install_authorized: false
    test_execution_authorized: false
    can_proceed_to_track_3_inventory_and_audit_execution: true

  this_artifact:
    executes_dependency_inventory: true
    executes_dependency_audit: true
    executes_pip_audit: true
    changes_dependencies: false
    installs_packages: false
    runs_tests: false
    executes_runtime: false
```

## 3. Current Governed State

```yaml
current_state:
  system_state: SAFE_PRE_CROSSING
  hold_status: HOLD_CRITICAL_PRESERVED

  Wave_5_opened: true
  Track_1_AUTH_BOUNDARY: remediated_with_monitoring_pending_final_wave_5_retest
  Track_2_F_004_CONFIG_HARDENING: remediated_with_monitoring_pending_final_wave_5_retest
  active_security_track: F_005_DEPENDENCY_SECURITY
  current_step: track_3_dependency_security_inventory_and_audit_execution

  production_ready: false
  runtime_integration_authorized: false
  runtime_execution_authorized: false
  wave_5_operational_start_authorized: false
  application_external_call_authorized: false
  credential_access_authorized: false
```

## 4. Dependency Inventory

```yaml
dependency_inventory:
  command:
    - rg --files -g 'requirements*.txt' -g 'pyproject.toml' -g 'poetry.lock' -g 'uv.lock' -g 'Pipfile' -g 'Pipfile.lock' -g 'Dockerfile' -g 'docker-compose*.yml' -g 'docker-compose*.yaml' -g '.github/workflows/*'

  discovered_surfaces:
    python_dependency_manifests:
      - backend/requirements.txt

    container_dependency_surfaces:
      - backend/Dockerfile
      - docker-compose.yml

    lock_or_constraints_files: []
    root_python_manifest_detected: false
    pyproject_detected: false
    poetry_lock_detected: false
    uv_lock_detected: false
    pipfile_detected: false
    github_workflow_dependency_surface_detected: false

  authoritative_manifest_for_this_audit: backend/requirements.txt
  inventory_result: completed
```

## 5. Audit Tool Availability

```yaml
audit_tool_availability:
  commands:
    - python -m pip_audit --version
    - pip-audit --version

  result:
    pip_audit_available: true
    pip_audit_version: 2.10.0
```

## 6. Dependency Audit Execution

```yaml
dependency_audit_execution:
  command:
    - pip-audit -r backend/requirements.txt --format json --progress-spinner off

  audited_manifest: backend/requirements.txt
  tool: pip-audit
  tool_version: 2.10.0
  exit_code: 1
  exit_code_interpretation: completed_with_vulnerability_findings
  result: completed_with_findings

  summary:
    vulnerable_packages: 5
    vulnerabilities: 6
    fixes_array_empty_in_json: true
    severity_counts_available_from_tool_output: false
```

`pip-audit` returned exit code `1` because vulnerabilities were found. No dependency files were changed by the audit.

## 7. Vulnerability Findings

```yaml
vulnerability_findings:
  - package: python-multipart
    current_version: 0.0.22
    vulnerability_id: CVE-2026-40347
    aliases:
      - GHSA-mj87-hwqh-73pj
    fix_versions:
      - 0.0.26
    impact_summary: crafted_multipart_form_data_can_cause_excessive_CPU_during_parsing

  - package: cryptography
    current_version: 46.0.5
    vulnerability_id: CVE-2026-34073
    aliases:
      - GHSA-m959-cc7f-wv43
    fix_versions:
      - 46.0.6
    impact_summary: certificate_name_constraints_validation_bypass_in_uncommon_X509_topology

  - package: cryptography
    current_version: 46.0.5
    vulnerability_id: CVE-2026-39892
    aliases:
      - GHSA-p423-j2cm-9vmq
    fix_versions:
      - 46.0.7
    impact_summary: non_contiguous_buffer_input_can_trigger_buffer_overread

  - package: python-dotenv
    current_version: 1.0.1
    vulnerability_id: CVE-2026-28684
    aliases:
      - GHSA-mf9w-mj56-hr94
    fix_versions:
      - 1.2.2
    impact_summary: set_key_or_unset_key_can_follow_symlinks_and_overwrite_files_under_specific_conditions

  - package: pytest
    current_version: 8.2.2
    vulnerability_id: CVE-2025-71176
    aliases:
      - GHSA-6w46-j5rx-g56g
    fix_versions:
      - 9.0.3
    impact_summary: UNIX_tmp_pytest_directory_pattern_can_allow_local_DoS_or_possible_privilege_impact

  - package: pillow
    current_version: 12.1.1
    vulnerability_id: CVE-2026-40192
    aliases:
      - GHSA-whj4-6x5x-4v2j
    fix_versions:
      - 12.2.0
    impact_summary: FITS_image_GZIP_decompression_bomb_can_cause_unbounded_memory_consumption
```

## 8. Remediation Candidate Set

```yaml
remediation_candidate_set:
  minimal_candidate_version_changes_for_future_authorization:
    python-multipart: 0.0.26
    cryptography: 46.0.7
    python-dotenv: 1.2.2
    pytest: 9.0.3
    pillow: 12.2.0

  rationale:
    - selected_versions_are_lowest_fix_versions_reported_by_pip_audit_or_highest_needed_for_multiple_findings
    - cryptography_requires_46_0_7_to_cover_both_reported_findings
    - dependency_patch_requires_separate_authorization_and_review
```

## 9. Non-Execution Evidence

```yaml
non_execution_evidence:
  dependency_files_changed_by_this_step: false
  requirements_change_performed: false
  lockfile_change_performed: false
  package_install_performed: false
  package_upgrade_performed: false
  tests_executed: false
  runtime_executed: false
  application_external_calls_performed: false
  credentials_accessed: false
  env_values_read: false
  production_ready_declared: false
```

## 10. Guardrail Preservation

```yaml
guardrail_preservation:
  SAFE_PRE_CROSSING: preserved
  HOLD_CRITICAL_PRESERVED: preserved

  dependency_change_authorized: false
  requirements_change_authorized: false
  lockfile_change_authorized: false
  package_install_authorized: false
  package_upgrade_authorized: false
  test_execution_authorized: false
  runtime_integration_authorized: false
  runtime_execution_authorized: false
  wave_5_operational_start_authorized: false
  application_external_call_authorized: false
  credential_access_authorized: false
  production_ready: false

  result: PASS
```

## 11. Execution Decision

```yaml
execution_decision:
  inventory_execution_completed: true
  dependency_audit_execution_completed: true
  pip_audit_execution_completed: true
  result: COMPLETED_WITH_FINDINGS

  F_005_dependency_security_status: findings_confirmed_pending_remediation_patch_authorization
  dependency_remediation_patch_required: true

  reason:
    - authoritative_manifest_for_audit_was_identified
    - pip_audit_completed_successfully_enough_to_report_findings
    - six_vulnerabilities_were_reported_across_five_packages
    - remediation_candidates_are_identified_but_not_applied
    - dependency_changes_require_separate_authorization
```

## 12. Required Next Artifact

```yaml
next_artifact:
  name: CortAI Full Repo Critical Checklist Wave 5 Track 3 F-005 DEPENDENCY SECURITY Inventory And Audit Execution Review
  path: docs/runtime/wave-5/security-remediation/CortAI_Full_Repo_Critical_Checklist_Wave_5_Track_3_F_005_DEPENDENCY_SECURITY_Inventory_And_Audit_Execution_Review.md
  purpose:
    - review_dependency_inventory_and_audit_results
    - accept_or_reject_pip_audit_findings
    - confirm_no_dependency_changes_were_performed
    - decide_whether_dependency_remediation_patch_authorization_can_be_created
```

## 13. Final Verdict

```yaml
final_verdict:
  inventory_execution_completed: true
  dependency_audit_execution_completed: true
  pip_audit_execution_completed: true
  audit_result: COMPLETED_WITH_FINDINGS
  vulnerable_packages: 5
  vulnerabilities: 6

  vulnerable_package_set:
    - python-multipart
    - cryptography
    - python-dotenv
    - pytest
    - pillow

  dependency_remediation_patch_required: true
  dependency_change_performed: false
  package_install_performed: false
  package_upgrade_performed: false
  test_execution_performed: false
  runtime_execution_performed: false
  production_ready: false

  SAFE_PRE_CROSSING_preserved: true
  HOLD_CRITICAL_PRESERVED: true

  next_artifact: CortAI Full Repo Critical Checklist Wave 5 Track 3 F-005 DEPENDENCY SECURITY Inventory And Audit Execution Review
```
