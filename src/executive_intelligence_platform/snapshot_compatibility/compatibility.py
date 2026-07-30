"""Fail-closed compatibility checks for externally owned snapshots.

The ExecutiveAssessmentSnapshot contract is owned by the Assessment Service.
This module validates serialized artifacts against the approved producer-owned
contract signals without generating, mutating, normalizing, or repairing them.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping


SUPPORTED_RESPONSE_CONTRACT_VERSION = "executive-runtime-response-v1"
SUPPORTED_PACKAGE_CONTRACT_VERSION = "business-decision-package-v1"
SUPPORTED_ASSESSMENT_VERSION = "nguyen-ai-executive-assessment-v1"
SUPPORTED_METHODOLOGY_VERSION = "business-decision-methodology-v1"

ROOT_FIELD_ORDER = (
    "responseContractVersion",
    "responseStatus",
    "businessDecisionPackage",
)
RESPONSE_STATUS_FIELD_ORDER = (
    "packageValidation",
    "runtimeEligibility",
    "exposure",
    "productionAuthority",
)
PACKAGE_FIELD_ORDER = (
    "decisionEvaluation",
    "businessReadinessSnapshot",
    "confidenceEvaluation",
    "recommendationPriorityEvaluation",
    "executiveSummaryFoundation",
    "audit",
    "limitations",
    "versionMetadata",
)
PACKAGE_COMPONENT_FIELDS = (
    "decisionEvaluation",
    "businessReadinessSnapshot",
    "confidenceEvaluation",
    "recommendationPriorityEvaluation",
    "executiveSummaryFoundation",
)
PACKAGE_SOURCE_COMPONENTS = (
    "decisionEvaluation",
    "businessReadinessSnapshot",
    "confidenceEvaluation",
    "recommendationPriorityEvaluation",
    "executiveSummaryFoundation",
)
PACKAGE_COMPONENT_VERSIONS = {
    "decisionEvaluation": "assessment-decision-engine-v2",
    "businessReadinessSnapshot": "sprint3-snapshot-foundation-v1",
    "confidenceEvaluation": "sprint3-confidence-foundation-v1",
    "recommendationPriorityEvaluation": (
        "sprint3-recommendation-priority-foundation-v1"
    ),
    "executiveSummaryFoundation": "sprint3-executive-summary-foundation-v1",
}
PACKAGE_LIMITATIONS = (
    "final-confidence-formulas-not-implemented",
    "final-confidence-level-assignment-not-implemented",
    "final-recommendation-assignment-not-implemented",
    "recommendation-generation-not-implemented",
    "service-decisions-not-implemented",
    "executive-reporting-not-implemented",
    "executive-narratives-not-implemented",
    "evidence-ingestion-not-implemented",
    "persistence-not-implemented",
    "api-exposure-of-snapshot-consumers-not-implemented",
)
RESPONSE_STATUS_ALLOWED_VALUES = {
    "packageValidation": {"VALIDATED"},
    "runtimeEligibility": {"RUNTIME_ELIGIBLE"},
    "exposure": {"EXPOSURE_ELIGIBLE"},
    "productionAuthority": {
        "PRODUCTION_AUTHORITATIVE",
        "NOT_PRODUCTION_AUTHORITATIVE",
    },
}
SNAPSHOT_COMPATIBILITY_ISSUE_CODES = MappingProxyType(
    {
        "invalid-snapshot-serialization-type": (
            "Snapshot artifact is not a serialized mapping."
        ),
        "snapshot-field-order-mismatch": (
            "Snapshot root fields do not match the producer contract order."
        ),
        "missing-snapshot-field": (
            "Snapshot is missing a required producer contract field."
        ),
        "unexpected-snapshot-field": (
            "Snapshot contains a field outside the producer contract."
        ),
        "unsupported-response-contract-version": (
            "Snapshot response contract version is not supported."
        ),
        "invalid-response-status": (
            "Snapshot response status is missing or not a mapping."
        ),
        "response-status-field-order-mismatch": (
            "Response status fields do not match the producer contract order."
        ),
        "missing-response-status-field": (
            "Response status is missing a required producer contract field."
        ),
        "unexpected-response-status-field": (
            "Response status contains a field outside the producer contract."
        ),
        "unsupported-response-status": (
            "Response status contains a value outside supported compatibility policy."
        ),
        "invalid-business-decision-package": (
            "BusinessDecisionPackage is missing or not a serialized mapping."
        ),
        "package-field-order-mismatch": (
            "BusinessDecisionPackage fields do not match the producer contract order."
        ),
        "missing-package-field": (
            "BusinessDecisionPackage is missing a required producer contract field."
        ),
        "unexpected-package-field": (
            "BusinessDecisionPackage contains a field outside the producer contract."
        ),
        "missing-package-component": (
            "BusinessDecisionPackage is missing a required serialized component."
        ),
        "invalid-package-version-metadata": (
            "BusinessDecisionPackage version metadata is missing or not a mapping."
        ),
        "missing-package-version-metadata-field": (
            "BusinessDecisionPackage version metadata is missing a required field."
        ),
        "unsupported-package-contract-version": (
            "BusinessDecisionPackage contract version is not supported."
        ),
        "unsupported-assessment-version": (
            "Assessment version is not supported."
        ),
        "unsupported-methodology-version": (
            "Methodology version is not supported."
        ),
        "invalid-component-versions": (
            "Component versions are missing or not a mapping."
        ),
        "unsupported-component-versions": (
            "Component versions do not match supported compatibility policy."
        ),
        "invalid-package-audit": (
            "BusinessDecisionPackage audit is missing or not a mapping."
        ),
        "missing-package-audit-field": (
            "BusinessDecisionPackage audit is missing a required field."
        ),
        "unsupported-source-components": (
            "Audit source components do not match producer provenance."
        ),
        "audit-assessment-version-mismatch": (
            "Audit assessment version does not match version metadata."
        ),
        "audit-methodology-version-mismatch": (
            "Audit methodology version does not match version metadata."
        ),
        "invalid-package-limitations": (
            "BusinessDecisionPackage limitations are missing or not an array."
        ),
        "unsupported-package-limitations": (
            "BusinessDecisionPackage limitations do not match the producer contract."
        ),
        "duplicate-package-limitations": (
            "BusinessDecisionPackage limitations contain duplicate values."
        ),
        "decision-snapshot-score-mismatch": (
            "Readiness snapshot score does not match decision evaluation score."
        ),
        "decision-snapshot-question-count-mismatch": (
            "Readiness snapshot question count does not match decision evaluation."
        ),
        "decision-snapshot-total-weight-mismatch": (
            "Readiness snapshot total weight does not match decision evaluation."
        ),
    }
)


@dataclass(frozen=True)
class SnapshotCompatibilityIssue:
    code: str
    path: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "path": self.path,
            "message": self.message,
        }


@dataclass(frozen=True)
class SnapshotCompatibilityResult:
    is_valid: bool
    issues: tuple[SnapshotCompatibilityIssue, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "isValid": self.is_valid,
            "issues": [issue.to_dict() for issue in self.issues],
        }


def validate_snapshot_compatibility(
    snapshot: object,
) -> SnapshotCompatibilityResult:
    issues: list[SnapshotCompatibilityIssue] = []

    if not isinstance(snapshot, Mapping):
        issues.append(
            _issue(
                "invalid-snapshot-serialization-type",
                "$",
                "Serialized snapshot must be a mapping.",
            )
        )
        return _result(issues)

    _validate_root(snapshot, issues)
    _validate_response_contract_version(snapshot, issues)
    _validate_response_status(snapshot, issues)
    _validate_business_decision_package(snapshot, issues)

    return _result(issues)


def _validate_root(
    snapshot: Mapping[str, Any],
    issues: list[SnapshotCompatibilityIssue],
) -> None:
    _validate_field_order(
        snapshot,
        ROOT_FIELD_ORDER,
        "$",
        "snapshot-field-order-mismatch",
        "Serialized snapshot root fields do not match contract order.",
        issues,
    )
    _validate_required_and_unexpected_fields(
        snapshot,
        ROOT_FIELD_ORDER,
        "$",
        "missing-snapshot-field",
        "unexpected-snapshot-field",
        issues,
    )


def _validate_response_contract_version(
    snapshot: Mapping[str, Any],
    issues: list[SnapshotCompatibilityIssue],
) -> None:
    if snapshot.get("responseContractVersion") != SUPPORTED_RESPONSE_CONTRACT_VERSION:
        issues.append(
            _issue(
                "unsupported-response-contract-version",
                "$.responseContractVersion",
                "Snapshot response contract version is not supported.",
            )
        )


def _validate_response_status(
    snapshot: Mapping[str, Any],
    issues: list[SnapshotCompatibilityIssue],
) -> None:
    response_status = snapshot.get("responseStatus")
    if not isinstance(response_status, Mapping):
        issues.append(
            _issue(
                "invalid-response-status",
                "$.responseStatus",
                "Serialized response status must be a mapping.",
            )
        )
        return

    _validate_field_order(
        response_status,
        RESPONSE_STATUS_FIELD_ORDER,
        "$.responseStatus",
        "response-status-field-order-mismatch",
        "Serialized response status fields do not match contract order.",
        issues,
    )
    _validate_required_and_unexpected_fields(
        response_status,
        RESPONSE_STATUS_FIELD_ORDER,
        "$.responseStatus",
        "missing-response-status-field",
        "unexpected-response-status-field",
        issues,
    )

    for field_name, allowed_values in RESPONSE_STATUS_ALLOWED_VALUES.items():
        if response_status.get(field_name) not in allowed_values:
            issues.append(
                _issue(
                    "unsupported-response-status",
                    f"$.responseStatus.{field_name}",
                    "Serialized response status contains an unsupported value.",
                )
            )


def _validate_business_decision_package(
    snapshot: Mapping[str, Any],
    issues: list[SnapshotCompatibilityIssue],
) -> None:
    package = snapshot.get("businessDecisionPackage")
    if not isinstance(package, Mapping):
        issues.append(
            _issue(
                "invalid-business-decision-package",
                "$.businessDecisionPackage",
                "Serialized business decision package must be a mapping.",
            )
        )
        return

    _validate_field_order(
        package,
        PACKAGE_FIELD_ORDER,
        "$.businessDecisionPackage",
        "package-field-order-mismatch",
        "Serialized package fields do not match contract order.",
        issues,
    )
    _validate_required_and_unexpected_fields(
        package,
        PACKAGE_FIELD_ORDER,
        "$.businessDecisionPackage",
        "missing-package-field",
        "unexpected-package-field",
        issues,
    )
    _validate_package_component_presence(package, issues)
    _validate_package_version_metadata(package, issues)
    _validate_package_audit(package, issues)
    _validate_package_limitations(package, issues)
    _validate_package_invariants(package, issues)


def _validate_package_component_presence(
    package: Mapping[str, Any],
    issues: list[SnapshotCompatibilityIssue],
) -> None:
    for field_name in PACKAGE_COMPONENT_FIELDS:
        if package.get(field_name) is None:
            issues.append(
                _issue(
                    "missing-package-component",
                    f"$.businessDecisionPackage.{field_name}",
                    f"Serialized package component is missing: {field_name}.",
                )
            )


def _validate_package_version_metadata(
    package: Mapping[str, Any],
    issues: list[SnapshotCompatibilityIssue],
) -> None:
    metadata = package.get("versionMetadata")
    if not isinstance(metadata, Mapping):
        issues.append(
            _issue(
                "invalid-package-version-metadata",
                "$.businessDecisionPackage.versionMetadata",
                "Package version metadata must be a mapping.",
            )
        )
        return

    _validate_required_keys(
        metadata,
        (
            "contractVersion",
            "assessmentVersion",
            "methodologyVersion",
            "componentVersions",
        ),
        "$.businessDecisionPackage.versionMetadata",
        "missing-package-version-metadata-field",
        issues,
    )

    if metadata.get("contractVersion") != SUPPORTED_PACKAGE_CONTRACT_VERSION:
        issues.append(
            _issue(
                "unsupported-package-contract-version",
                "$.businessDecisionPackage.versionMetadata.contractVersion",
                "Package contract version is not supported.",
            )
        )
    if metadata.get("assessmentVersion") != SUPPORTED_ASSESSMENT_VERSION:
        issues.append(
            _issue(
                "unsupported-assessment-version",
                "$.businessDecisionPackage.versionMetadata.assessmentVersion",
                "Assessment version is not supported.",
            )
        )
    if metadata.get("methodologyVersion") != SUPPORTED_METHODOLOGY_VERSION:
        issues.append(
            _issue(
                "unsupported-methodology-version",
                "$.businessDecisionPackage.versionMetadata.methodologyVersion",
                "Methodology version is not supported.",
            )
        )

    component_versions = metadata.get("componentVersions")
    if not isinstance(component_versions, Mapping):
        issues.append(
            _issue(
                "invalid-component-versions",
                "$.businessDecisionPackage.versionMetadata.componentVersions",
                "Component versions must be a mapping.",
            )
        )
        return

    if dict(component_versions) != PACKAGE_COMPONENT_VERSIONS:
        issues.append(
            _issue(
                "unsupported-component-versions",
                "$.businessDecisionPackage.versionMetadata.componentVersions",
                "Component versions are not supported.",
            )
        )


def _validate_package_audit(
    package: Mapping[str, Any],
    issues: list[SnapshotCompatibilityIssue],
) -> None:
    audit = package.get("audit")
    if not isinstance(audit, Mapping):
        issues.append(
            _issue(
                "invalid-package-audit",
                "$.businessDecisionPackage.audit",
                "Package audit must be a mapping.",
            )
        )
        return

    _validate_required_keys(
        audit,
        (
            "assessmentVersion",
            "methodologyVersion",
            "sourceComponentIds",
            "evaluatedDimensions",
            "questionCount",
            "totalWeight",
        ),
        "$.businessDecisionPackage.audit",
        "missing-package-audit-field",
        issues,
    )

    if tuple(audit.get("sourceComponentIds", ())) != PACKAGE_SOURCE_COMPONENTS:
        issues.append(
            _issue(
                "unsupported-source-components",
                "$.businessDecisionPackage.audit.sourceComponentIds",
                "Audit source components do not match the producer contract.",
            )
        )

    metadata = package.get("versionMetadata")
    if isinstance(metadata, Mapping):
        if audit.get("assessmentVersion") != metadata.get("assessmentVersion"):
            issues.append(
                _issue(
                    "audit-assessment-version-mismatch",
                    "$.businessDecisionPackage.audit.assessmentVersion",
                    "Audit assessment version does not match version metadata.",
                )
            )
        if audit.get("methodologyVersion") != metadata.get("methodologyVersion"):
            issues.append(
                _issue(
                    "audit-methodology-version-mismatch",
                    "$.businessDecisionPackage.audit.methodologyVersion",
                    "Audit methodology version does not match version metadata.",
                )
            )


def _validate_package_limitations(
    package: Mapping[str, Any],
    issues: list[SnapshotCompatibilityIssue],
) -> None:
    limitations = package.get("limitations")
    if not isinstance(limitations, list):
        issues.append(
            _issue(
                "invalid-package-limitations",
                "$.businessDecisionPackage.limitations",
                "Package limitations must be an array.",
            )
        )
        return

    if tuple(limitations) != PACKAGE_LIMITATIONS:
        issues.append(
            _issue(
                "unsupported-package-limitations",
                "$.businessDecisionPackage.limitations",
                "Package limitations do not match the producer contract.",
            )
        )
    if len(limitations) != len(set(limitations)):
        issues.append(
            _issue(
                "duplicate-package-limitations",
                "$.businessDecisionPackage.limitations",
                "Package limitations contain duplicate values.",
            )
        )


def _validate_package_invariants(
    package: Mapping[str, Any],
    issues: list[SnapshotCompatibilityIssue],
) -> None:
    decision_evaluation = package.get("decisionEvaluation")
    readiness_snapshot = package.get("businessReadinessSnapshot")
    if not isinstance(decision_evaluation, Mapping) or not isinstance(
        readiness_snapshot,
        Mapping,
    ):
        return

    overall_readiness = readiness_snapshot.get("overallReadiness")
    if isinstance(overall_readiness, Mapping):
        if overall_readiness.get("score") != decision_evaluation.get("overallScore"):
            issues.append(
                _issue(
                    "decision-snapshot-score-mismatch",
                    "$.businessDecisionPackage.businessReadinessSnapshot.overallReadiness.score",
                    "Snapshot readiness score does not match decision score.",
                )
            )

    snapshot_audit = readiness_snapshot.get("audit")
    if isinstance(snapshot_audit, Mapping):
        if snapshot_audit.get("questionCount") != decision_evaluation.get(
            "questionCount"
        ):
            issues.append(
                _issue(
                    "decision-snapshot-question-count-mismatch",
                    "$.businessDecisionPackage.businessReadinessSnapshot.audit.questionCount",
                    "Snapshot question count does not match decision evaluation.",
                )
            )
        if snapshot_audit.get("totalWeight") != decision_evaluation.get(
            "totalWeight"
        ):
            issues.append(
                _issue(
                    "decision-snapshot-total-weight-mismatch",
                    "$.businessDecisionPackage.businessReadinessSnapshot.audit.totalWeight",
                    "Snapshot total weight does not match decision evaluation.",
                )
            )


def _validate_field_order(
    value: Mapping[str, Any],
    expected_order: tuple[str, ...],
    path: str,
    code: str,
    message: str,
    issues: list[SnapshotCompatibilityIssue],
) -> None:
    if tuple(value) != expected_order:
        issues.append(_issue(code, path, message))


def _validate_required_and_unexpected_fields(
    value: Mapping[str, Any],
    expected_fields: tuple[str, ...],
    path: str,
    missing_code: str,
    unexpected_code: str,
    issues: list[SnapshotCompatibilityIssue],
) -> None:
    observed = set(value)
    expected = set(expected_fields)
    for field_name in sorted(expected - observed):
        issues.append(
            _issue(
                missing_code,
                f"{path}.{field_name}",
                f"Required field is missing: {field_name}.",
            )
        )
    for field_name in sorted(observed - expected):
        issues.append(
            _issue(
                unexpected_code,
                f"{path}.{field_name}",
                f"Unexpected field is present: {field_name}.",
            )
        )


def _validate_required_keys(
    value: Mapping[str, Any],
    required_keys: tuple[str, ...],
    path: str,
    code: str,
    issues: list[SnapshotCompatibilityIssue],
) -> None:
    for key in required_keys:
        if key not in value:
            issues.append(
                _issue(
                    code,
                    f"{path}.{key}",
                    f"Required field is missing: {key}.",
                )
            )


def _issue(code: str, path: str, message: str) -> SnapshotCompatibilityIssue:
    if code not in SNAPSHOT_COMPATIBILITY_ISSUE_CODES:
        raise ValueError(f"Undocumented snapshot compatibility issue code: {code}.")
    return SnapshotCompatibilityIssue(code=code, path=path, message=message)


def _result(
    issues: list[SnapshotCompatibilityIssue],
) -> SnapshotCompatibilityResult:
    return SnapshotCompatibilityResult(
        is_valid=not issues,
        issues=tuple(issues),
    )
