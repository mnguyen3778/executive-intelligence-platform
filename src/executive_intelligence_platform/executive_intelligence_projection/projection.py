"""Immutable Executive Intelligence Projection foundation.

Projection consumes exactly one ExecutiveIntelligencePackage and exposes
deterministic package metadata and lineage without adding presentation,
reporting, dashboard, or business-calculation behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from executive_intelligence_platform.executive_intelligence_package import (
    EXECUTIVE_INTELLIGENCE_PACKAGE_ASSEMBLY_RULE_VERSION,
    EXECUTIVE_INTELLIGENCE_PACKAGE_CONTRACT_VERSION,
    ExecutiveIntelligencePackage,
    ExecutiveIntelligencePackageLineage,
)


EXECUTIVE_INTELLIGENCE_PROJECTION_CONTRACT_VERSION = (
    "executive-intelligence-projection-v1"
)
EXECUTIVE_INTELLIGENCE_PROJECTION_RULE_VERSION = (
    "executive-intelligence-canonical-projection-v1"
)
EXECUTIVE_INTELLIGENCE_PROJECTION_ISSUE_CODES = MappingProxyType(
    {
        "invalid-projection-request": (
            "Executive Intelligence Projection request is missing or invalid."
        ),
        "unsupported-projection-contract-version": (
            "Requested Executive Intelligence Projection contract version is not supported."
        ),
        "unsupported-projection-rule": (
            "Requested Executive Intelligence Projection rule is not supported."
        ),
        "invalid-executive-intelligence-package": (
            "Projection input is not an ExecutiveIntelligencePackage."
        ),
        "incomplete-package-lineage": (
            "Executive Intelligence Package lineage is incomplete for projection."
        ),
        "inconsistent-package-lineage": (
            "Executive Intelligence Package lineage references are inconsistent."
        ),
        "unsupported-package-contract-version": (
            "Executive Intelligence Package contract version is not supported."
        ),
        "unsupported-package-assembly-rule": (
            "Executive Intelligence Package assembly rule is not supported."
        ),
    }
)


@dataclass(frozen=True)
class ExecutiveIntelligenceProjectionIssue:
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
class ExecutiveIntelligenceProjectionRequest:
    projection_contract_version: str = (
        EXECUTIVE_INTELLIGENCE_PROJECTION_CONTRACT_VERSION
    )
    projection_rule_version: str = EXECUTIVE_INTELLIGENCE_PROJECTION_RULE_VERSION

    def to_dict(self) -> dict[str, str]:
        return {
            "projectionContractVersion": self.projection_contract_version,
            "projectionRuleVersion": self.projection_rule_version,
        }


@dataclass(frozen=True)
class ExecutiveIntelligenceProjectionLineage:
    projection_contract_version: str
    projection_rule_version: str
    package_contract_version: str
    package_assembly_rule_version: str
    producer_snapshot_identity: str
    snapshot_contract_version: str
    assessment_version: str
    methodology_version: str
    derivation_rule_version: str
    derivation_runtime_version: str
    package_lineage: ExecutiveIntelligencePackageLineage

    def to_dict(self) -> dict[str, Any]:
        return {
            "projectionContractVersion": self.projection_contract_version,
            "projectionRuleVersion": self.projection_rule_version,
            "packageContractVersion": self.package_contract_version,
            "packageAssemblyRuleVersion": self.package_assembly_rule_version,
            "producerSnapshotIdentity": self.producer_snapshot_identity,
            "snapshotContractVersion": self.snapshot_contract_version,
            "assessmentVersion": self.assessment_version,
            "methodologyVersion": self.methodology_version,
            "derivationRuleVersion": self.derivation_rule_version,
            "derivationRuntimeVersion": self.derivation_runtime_version,
            "packageLineage": self.package_lineage.to_dict(),
        }


@dataclass(frozen=True)
class ExecutiveIntelligenceProjection:
    projection_contract_version: str
    projection_rule_version: str
    package_contract_version: str
    package_assembly_rule_version: str
    producer_snapshot_identity: str
    snapshot_contract_version: str
    assessment_version: str
    methodology_version: str
    derivation_rule_version: str
    derivation_runtime_version: str
    lineage: ExecutiveIntelligenceProjectionLineage
    source_package: ExecutiveIntelligencePackage

    def to_dict(self) -> dict[str, Any]:
        return {
            "projectionContractVersion": self.projection_contract_version,
            "projectionRuleVersion": self.projection_rule_version,
            "packageContractVersion": self.package_contract_version,
            "packageAssemblyRuleVersion": self.package_assembly_rule_version,
            "producerSnapshotIdentity": self.producer_snapshot_identity,
            "snapshotContractVersion": self.snapshot_contract_version,
            "assessmentVersion": self.assessment_version,
            "methodologyVersion": self.methodology_version,
            "derivationRuleVersion": self.derivation_rule_version,
            "derivationRuntimeVersion": self.derivation_runtime_version,
            "lineage": self.lineage.to_dict(),
            "sourcePackage": self.source_package.to_dict(),
        }


@dataclass(frozen=True)
class ExecutiveIntelligenceProjectionResult:
    projected: bool
    projection: ExecutiveIntelligenceProjection | None
    issues: tuple[ExecutiveIntelligenceProjectionIssue, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "projected": self.projected,
            "projection": (
                self.projection.to_dict() if self.projection is not None else None
            ),
            "issues": [issue.to_dict() for issue in self.issues],
        }


class ExecutiveIntelligenceProjectionProjector:
    """Minimal deterministic projector for one Executive Intelligence Package."""

    def project(
        self,
        request: object,
        package: object,
    ) -> ExecutiveIntelligenceProjectionResult:
        issues: list[ExecutiveIntelligenceProjectionIssue] = []
        issues.extend(_validate_request(request))

        if not isinstance(package, ExecutiveIntelligencePackage):
            issues.append(
                _issue(
                    "invalid-executive-intelligence-package",
                    "$.package",
                    "Projection input must be an ExecutiveIntelligencePackage.",
                )
            )
            return _result(False, None, issues)

        issues.extend(_validate_package(package))
        if issues:
            return _result(False, None, issues)

        if not isinstance(request, ExecutiveIntelligenceProjectionRequest):
            return _result(False, None, issues)

        return _result(True, _project_package(request, package), [])


def _validate_request(
    request: object,
) -> list[ExecutiveIntelligenceProjectionIssue]:
    if not isinstance(request, ExecutiveIntelligenceProjectionRequest):
        return [
            _issue(
                "invalid-projection-request",
                "$.request",
                "Projection request must be an ExecutiveIntelligenceProjectionRequest.",
            )
        ]

    issues: list[ExecutiveIntelligenceProjectionIssue] = []
    if (
        request.projection_contract_version
        != EXECUTIVE_INTELLIGENCE_PROJECTION_CONTRACT_VERSION
    ):
        issues.append(
            _issue(
                "unsupported-projection-contract-version",
                "$.request.projectionContractVersion",
                "Projection contract version is not supported.",
            )
        )
    if request.projection_rule_version != EXECUTIVE_INTELLIGENCE_PROJECTION_RULE_VERSION:
        issues.append(
            _issue(
                "unsupported-projection-rule",
                "$.request.projectionRuleVersion",
                "Projection rule version is not supported.",
            )
        )
    return issues


def _validate_package(
    package: ExecutiveIntelligencePackage,
) -> list[ExecutiveIntelligenceProjectionIssue]:
    issues: list[ExecutiveIntelligenceProjectionIssue] = []
    if package.package_contract_version != EXECUTIVE_INTELLIGENCE_PACKAGE_CONTRACT_VERSION:
        issues.append(
            _issue(
                "unsupported-package-contract-version",
                "$.package.packageContractVersion",
                "Package contract version is not supported.",
            )
        )
    if (
        package.package_assembly_rule_version
        != EXECUTIVE_INTELLIGENCE_PACKAGE_ASSEMBLY_RULE_VERSION
    ):
        issues.append(
            _issue(
                "unsupported-package-assembly-rule",
                "$.package.packageAssemblyRuleVersion",
                "Package assembly rule version is not supported.",
            )
        )

    issues.extend(_validate_package_lineage_completeness(package))
    if issues:
        return issues
    issues.extend(_validate_package_lineage_consistency(package))
    return issues


def _validate_package_lineage_completeness(
    package: ExecutiveIntelligencePackage,
) -> list[ExecutiveIntelligenceProjectionIssue]:
    issues: list[ExecutiveIntelligenceProjectionIssue] = []
    required_strings = {
        "producer_snapshot_identity": package.producer_snapshot_identity,
        "snapshot_contract_version": package.snapshot_contract_version,
        "assessment_version": package.assessment_version,
        "methodology_version": package.methodology_version,
        "derivation_rule_version": package.derivation_rule_version,
        "derivation_runtime_version": package.derivation_runtime_version,
    }
    for field_name, value in required_strings.items():
        if not isinstance(value, str) or not value.strip():
            issues.append(
                _issue(
                    "incomplete-package-lineage",
                    f"$.package.{field_name}",
                    "Package lineage field is incomplete.",
                )
            )

    if not isinstance(package.lineage, ExecutiveIntelligencePackageLineage):
        issues.append(
            _issue(
                "incomplete-package-lineage",
                "$.package.lineage",
                "Package lineage is missing.",
            )
        )
    return issues


def _validate_package_lineage_consistency(
    package: ExecutiveIntelligencePackage,
) -> list[ExecutiveIntelligenceProjectionIssue]:
    issues: list[ExecutiveIntelligenceProjectionIssue] = []
    lineage = package.lineage

    checks = (
        (
            package.producer_snapshot_identity,
            lineage.producer_snapshot_identity,
            "$.package.lineage.producerSnapshotIdentity",
        ),
        (
            package.snapshot_contract_version,
            lineage.snapshot_contract_version,
            "$.package.lineage.snapshotContractVersion",
        ),
        (
            package.assessment_version,
            lineage.assessment_version,
            "$.package.lineage.assessmentVersion",
        ),
        (
            package.methodology_version,
            lineage.methodology_version,
            "$.package.lineage.methodologyVersion",
        ),
        (
            package.derivation_rule_version,
            lineage.derivation_rule_version,
            "$.package.lineage.derivationRuleVersion",
        ),
        (
            package.derivation_runtime_version,
            lineage.derivation_runtime_version,
            "$.package.lineage.derivationRuntimeVersion",
        ),
        (
            package.producer_snapshot_identity,
            lineage.catalog_admission_metadata.producer_snapshot_identity,
            "$.package.lineage.catalogAdmissionMetadata.producerSnapshotIdentity",
        ),
        (
            package.producer_snapshot_identity,
            lineage.producer_provenance.producer_snapshot_identity,
            "$.package.lineage.producerProvenance.producerSnapshotIdentity",
        ),
    )
    for left, right, path in checks:
        if left != right:
            issues.append(
                _issue(
                    "inconsistent-package-lineage",
                    path,
                    "Package lineage references are inconsistent.",
                )
            )

    if tuple(lineage.catalog_admission_metadata.source_component_ids) != tuple(
        lineage.producer_provenance.source_component_ids
    ):
        issues.append(
            _issue(
                "inconsistent-package-lineage",
                "$.package.lineage.producerProvenance.sourceComponentIds",
                "Package source component lineage is inconsistent.",
            )
        )
    if lineage.catalog_admission_metadata.production_authority != (
        lineage.producer_provenance.production_authority
    ):
        issues.append(
            _issue(
                "inconsistent-package-lineage",
                "$.package.lineage.producerProvenance.productionAuthority",
                "Package production authority lineage is inconsistent.",
            )
        )

    return issues


def _project_package(
    request: ExecutiveIntelligenceProjectionRequest,
    package: ExecutiveIntelligencePackage,
) -> ExecutiveIntelligenceProjection:
    lineage = ExecutiveIntelligenceProjectionLineage(
        projection_contract_version=request.projection_contract_version,
        projection_rule_version=request.projection_rule_version,
        package_contract_version=package.package_contract_version,
        package_assembly_rule_version=package.package_assembly_rule_version,
        producer_snapshot_identity=package.producer_snapshot_identity,
        snapshot_contract_version=package.snapshot_contract_version,
        assessment_version=package.assessment_version,
        methodology_version=package.methodology_version,
        derivation_rule_version=package.derivation_rule_version,
        derivation_runtime_version=package.derivation_runtime_version,
        package_lineage=package.lineage,
    )
    return ExecutiveIntelligenceProjection(
        projection_contract_version=request.projection_contract_version,
        projection_rule_version=request.projection_rule_version,
        package_contract_version=package.package_contract_version,
        package_assembly_rule_version=package.package_assembly_rule_version,
        producer_snapshot_identity=package.producer_snapshot_identity,
        snapshot_contract_version=package.snapshot_contract_version,
        assessment_version=package.assessment_version,
        methodology_version=package.methodology_version,
        derivation_rule_version=package.derivation_rule_version,
        derivation_runtime_version=package.derivation_runtime_version,
        lineage=lineage,
        source_package=package,
    )


def _issue(
    code: str,
    path: str,
    message: str,
) -> ExecutiveIntelligenceProjectionIssue:
    if code not in EXECUTIVE_INTELLIGENCE_PROJECTION_ISSUE_CODES:
        raise ValueError(f"Undocumented Executive Intelligence Projection issue: {code}.")
    return ExecutiveIntelligenceProjectionIssue(code=code, path=path, message=message)


def _result(
    projected: bool,
    projection: ExecutiveIntelligenceProjection | None,
    issues: list[ExecutiveIntelligenceProjectionIssue],
) -> ExecutiveIntelligenceProjectionResult:
    return ExecutiveIntelligenceProjectionResult(
        projected=projected,
        projection=projection,
        issues=tuple(issues),
    )
