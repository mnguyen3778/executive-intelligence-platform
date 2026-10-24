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
GOVERNED_PACKAGE_CONTRACT_VERSION = "business-decision-package-v2"
GOVERNED_ASSESSMENT_VERSION = "nguyen-ai-executive-assessment-v2"
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
GOVERNED_PACKAGE_FIELD_ORDER = PACKAGE_FIELD_ORDER + ("governedConclusions",)
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
GOVERNED_PACKAGE_LIMITATIONS = PACKAGE_LIMITATIONS[4:]
GOVERNED_CONCLUSION_FIELDS = (
    "severityAssignedFindings", "assessmentRisk", "confidence",
    "recommendations", "executiveSummary",
)
GOVERNED_FINDING_FIELDS = (
    "findingId", "title", "primaryDimension", "relatedDimensions",
    "triggerSource", "findingType", "businessConsequenceBasis",
    "sourceReferences", "sequenceIdentifier", "severityClassification",
    "severityDecisionIdentifier", "severityDecisionTableVersion",
)
GOVERNED_RECOMMENDATION_FIELDS = (
    "findingId", "recommendationClassification",
    "recommendationDecisionIdentifier", "recommendationDecisionTableVersion",
)
GOVERNED_SUMMARY_SECTIONS = (
    "overall-assessment-overview", "business-capability-highlights",
    "significant-findings", "risk-overview", "confidence-statement",
    "recommended-actions", "closing-assessment-statement",
)
GOVERNED_DIMENSIONS = frozenset(("POC", "GCR", "TISM", "DPSC", "RVCI"))
GOVERNED_CLASSIFICATIONS = {
    "severityClassification": frozenset(("critical", "high", "medium", "low", "informational")),
    "riskClassification": frozenset(("critical-risk", "elevated-risk", "moderate-risk", "low-risk", "minimal-informational")),
    "confidenceClassification": frozenset(("very-high-confidence", "high-confidence", "moderate-confidence", "low-confidence", "insufficient-confidence")),
    "recommendationClassification": frozenset(("immediate-action", "priority-action", "planned-improvement", "best-practice", "monitor")),
}
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
        "invalid-governed-conclusions": (
            "Governed conclusions do not match the frozen producer serialization contract."
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
        value = response_status.get(field_name)
        if not isinstance(value, str) or value not in allowed_values:
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

    metadata = package.get("versionMetadata")
    governed = isinstance(metadata, Mapping) and metadata.get("contractVersion") == GOVERNED_PACKAGE_CONTRACT_VERSION
    field_order = GOVERNED_PACKAGE_FIELD_ORDER if governed else PACKAGE_FIELD_ORDER
    _validate_field_order(
        package,
        field_order,
        "$.businessDecisionPackage",
        "package-field-order-mismatch",
        "Serialized package fields do not match contract order.",
        issues,
    )
    _validate_required_and_unexpected_fields(
        package,
        field_order,
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
    if governed:
        _validate_governed_conclusions(package.get("governedConclusions"), issues)


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

    contract_version = metadata.get("contractVersion")
    assessment_version = metadata.get("assessmentVersion")
    if contract_version not in (SUPPORTED_PACKAGE_CONTRACT_VERSION, GOVERNED_PACKAGE_CONTRACT_VERSION):
        issues.append(
            _issue(
                "unsupported-package-contract-version",
                "$.businessDecisionPackage.versionMetadata.contractVersion",
                "Package contract version is not supported.",
            )
        )
    expected_assessment = (
        GOVERNED_ASSESSMENT_VERSION if contract_version == GOVERNED_PACKAGE_CONTRACT_VERSION
        else SUPPORTED_ASSESSMENT_VERSION
    )
    if assessment_version != expected_assessment:
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

    source_components = audit.get("sourceComponentIds")
    if not isinstance(source_components, (list, tuple)) or tuple(source_components) != PACKAGE_SOURCE_COMPONENTS:
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

    metadata = package.get("versionMetadata")
    governed = isinstance(metadata, Mapping) and metadata.get("contractVersion") == GOVERNED_PACKAGE_CONTRACT_VERSION
    expected = GOVERNED_PACKAGE_LIMITATIONS if governed else PACKAGE_LIMITATIONS
    if tuple(limitations) != expected:
        issues.append(
            _issue(
                "unsupported-package-limitations",
                "$.businessDecisionPackage.limitations",
                "Package limitations do not match the producer contract.",
            )
        )
    if all(isinstance(item, str) for item in limitations) and len(limitations) != len(set(limitations)):
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


def _validate_governed_conclusions(
    value: object,
    issues: list[SnapshotCompatibilityIssue],
) -> None:
    try:
        valid = _governed_conclusions_match_contract(value)
    except (TypeError, ValueError):
        valid = False
    if not valid:
        issues.append(_issue(
            "invalid-governed-conclusions",
            "$.businessDecisionPackage.governedConclusions",
            "Governed conclusions are incomplete, malformed, or out of canonical order.",
        ))


def _ordered_mapping(value: object, fields: tuple[str, ...]) -> bool:
    return isinstance(value, Mapping) and tuple(value) == fields


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _canonical_references(value: object, *, required: bool = False) -> bool:
    return (
        isinstance(value, list)
        and (bool(value) or not required)
        and all(_text(item) for item in value)
        and value == sorted(set(value))
    )


def _governed_decision(
    value: object, fields: tuple[str, ...], classification: str,
    table_version: str,
) -> bool:
    return (
        _ordered_mapping(value, fields)
        and isinstance(value[classification], str)
        and value[classification] in GOVERNED_CLASSIFICATIONS[classification]
        and _text(value[fields[1]])
        and value[fields[2]] == table_version
    )


def _governed_conclusions_match_contract(value: object) -> bool:
    if not _ordered_mapping(value, GOVERNED_CONCLUSION_FIELDS):
        return False
    findings = value["severityAssignedFindings"]
    recommendations = value["recommendations"]
    if not isinstance(findings, list) or not isinstance(recommendations, list):
        return False
    finding_ids: list[str] = []
    for sequence, item in enumerate(findings, 1):
        if not _ordered_mapping(item, GOVERNED_FINDING_FIELDS):
            return False
        if not all(_text(item[key]) for key in (
            "findingId", "title", "triggerSource", "findingType",
            "businessConsequenceBasis", "severityDecisionIdentifier",
        )):
            return False
        if item["primaryDimension"] not in GOVERNED_DIMENSIONS:
            return False
        if not _canonical_references(item["relatedDimensions"]):
            return False
        if any(dimension not in GOVERNED_DIMENSIONS or dimension == item["primaryDimension"]
               for dimension in item["relatedDimensions"]):
            return False
        if not _canonical_references(item["sourceReferences"], required=True):
            return False
        if item["triggerSource"] not in item["sourceReferences"]:
            return False
        if type(item["sequenceIdentifier"]) is not int or item["sequenceIdentifier"] != sequence:
            return False
        if item["severityClassification"] not in GOVERNED_CLASSIFICATIONS["severityClassification"]:
            return False
        if item["severityDecisionTableVersion"] != "severity-decision-table-set-v1":
            return False
        finding_ids.append(item["findingId"])
    if finding_ids != sorted(set(finding_ids)):
        return False
    if not _governed_decision(
        value["assessmentRisk"],
        ("riskClassification", "riskDecisionIdentifier", "riskDecisionTableVersion"),
        "riskClassification", "risk-decision-table-set-v1",
    ) or not _governed_decision(
        value["confidence"],
        ("confidenceClassification", "confidenceDecisionIdentifier", "confidenceDecisionTableVersion"),
        "confidenceClassification", "confidence-decision-table-set-v1",
    ):
        return False
    if len(recommendations) != max(1, len(finding_ids)):
        return False
    for index, item in enumerate(recommendations):
        if not _ordered_mapping(item, GOVERNED_RECOMMENDATION_FIELDS):
            return False
        if item["findingId"] != (finding_ids[index] if finding_ids else None):
            return False
        if (item["recommendationClassification"] not in
                GOVERNED_CLASSIFICATIONS["recommendationClassification"]):
            return False
        if not _text(item["recommendationDecisionIdentifier"]):
            return False
        if item["recommendationDecisionTableVersion"] != "recommendation-decision-table-set-v1":
            return False
    if not finding_ids and (
        value["assessmentRisk"]["riskClassification"] != "minimal-informational"
        or recommendations[0]["recommendationDecisionIdentifier"] != "recommendation-v1-no-findings-monitor"
    ):
        return False
    summary = value["executiveSummary"]
    return (
        _ordered_mapping(summary, ("findingCount", "sectionText"))
        and type(summary["findingCount"]) is int
        and summary["findingCount"] == len(finding_ids)
        and _ordered_mapping(summary["sectionText"], GOVERNED_SUMMARY_SECTIONS)
        and all(_text(text) for text in summary["sectionText"].values())
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
