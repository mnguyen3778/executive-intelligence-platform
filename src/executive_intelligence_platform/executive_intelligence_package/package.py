"""Immutable Executive Intelligence Package assembly.

The package foundation consumes exactly one SnapshotDerivedArtifact and assembles
platform-owned package metadata without creating business identifiers,
recomputing assessment outputs, or implementing projection behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from executive_intelligence_platform.snapshot_catalog import SnapshotAdmissionMetadata
from executive_intelligence_platform.snapshot_derivation import (
    SnapshotCompatibilityValidationMetadata,
    SnapshotDerivedArtifact,
    SnapshotProducerProvenance,
)


EXECUTIVE_INTELLIGENCE_PACKAGE_CONTRACT_VERSION = "executive-intelligence-package-v1"
EXECUTIVE_INTELLIGENCE_PACKAGE_ASSEMBLY_RULE_VERSION = (
    "executive-intelligence-package-single-artifact-assembly-v1"
)
EXECUTIVE_INTELLIGENCE_PACKAGE_ISSUE_CODES = MappingProxyType(
    {
        "invalid-package-request": (
            "Executive Intelligence Package request is missing or invalid."
        ),
        "unsupported-package-contract-version": (
            "Requested Executive Intelligence Package contract version is not supported."
        ),
        "unsupported-package-assembly-rule": (
            "Requested Executive Intelligence Package assembly rule is not supported."
        ),
        "missing-derived-artifact": (
            "Executive Intelligence Package assembly requires one derived artifact."
        ),
        "multiple-derived-artifacts": (
            "Executive Intelligence Package assembly accepts exactly one derived artifact."
        ),
        "invalid-derived-artifact": (
            "Package input is not a SnapshotDerivedArtifact."
        ),
        "incomplete-derived-artifact-lineage": (
            "Derived artifact lineage is incomplete for package assembly."
        ),
        "inconsistent-derived-artifact-lineage": (
            "Derived artifact lineage references are inconsistent."
        ),
    }
)


@dataclass(frozen=True)
class ExecutiveIntelligencePackageIssue:
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
class ExecutiveIntelligencePackageRequest:
    package_contract_version: str = EXECUTIVE_INTELLIGENCE_PACKAGE_CONTRACT_VERSION
    package_assembly_rule_version: str = (
        EXECUTIVE_INTELLIGENCE_PACKAGE_ASSEMBLY_RULE_VERSION
    )

    def to_dict(self) -> dict[str, str]:
        return {
            "packageContractVersion": self.package_contract_version,
            "packageAssemblyRuleVersion": self.package_assembly_rule_version,
        }


@dataclass(frozen=True)
class ExecutiveIntelligencePackageLineage:
    producer_snapshot_identity: str
    snapshot_contract_version: str
    assessment_version: str
    methodology_version: str
    derivation_rule_version: str
    derivation_runtime_version: str
    catalog_admission_metadata: SnapshotAdmissionMetadata
    producer_provenance: SnapshotProducerProvenance

    def to_dict(self) -> dict[str, Any]:
        return {
            "producerSnapshotIdentity": self.producer_snapshot_identity,
            "snapshotContractVersion": self.snapshot_contract_version,
            "assessmentVersion": self.assessment_version,
            "methodologyVersion": self.methodology_version,
            "derivationRuleVersion": self.derivation_rule_version,
            "derivationRuntimeVersion": self.derivation_runtime_version,
            "catalogAdmissionMetadata": self.catalog_admission_metadata.to_dict(),
            "producerProvenance": self.producer_provenance.to_dict(),
        }


@dataclass(frozen=True)
class ExecutiveIntelligencePackage:
    package_contract_version: str
    package_assembly_rule_version: str
    producer_snapshot_identity: str
    snapshot_contract_version: str
    assessment_version: str
    methodology_version: str
    derivation_rule_version: str
    derivation_runtime_version: str
    lineage: ExecutiveIntelligencePackageLineage
    source_derived_artifact: SnapshotDerivedArtifact

    def to_dict(self) -> dict[str, Any]:
        return {
            "packageContractVersion": self.package_contract_version,
            "packageAssemblyRuleVersion": self.package_assembly_rule_version,
            "producerSnapshotIdentity": self.producer_snapshot_identity,
            "snapshotContractVersion": self.snapshot_contract_version,
            "assessmentVersion": self.assessment_version,
            "methodologyVersion": self.methodology_version,
            "derivationRuleVersion": self.derivation_rule_version,
            "derivationRuntimeVersion": self.derivation_runtime_version,
            "lineage": self.lineage.to_dict(),
            "sourceDerivedArtifact": self.source_derived_artifact.to_dict(),
        }


@dataclass(frozen=True)
class ExecutiveIntelligencePackageResult:
    packaged: bool
    package: ExecutiveIntelligencePackage | None
    issues: tuple[ExecutiveIntelligencePackageIssue, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "packaged": self.packaged,
            "package": self.package.to_dict() if self.package is not None else None,
            "issues": [issue.to_dict() for issue in self.issues],
        }


class ExecutiveIntelligencePackageAssembler:
    """Minimal deterministic package assembler for one derived artifact."""

    def assemble(
        self,
        request: object,
        *derived_artifacts: object,
    ) -> ExecutiveIntelligencePackageResult:
        issues: list[ExecutiveIntelligencePackageIssue] = []

        issues.extend(_validate_request(request))
        issues.extend(_validate_artifact_count(derived_artifacts))
        if issues:
            return _result(False, None, issues)

        derived_artifact = derived_artifacts[0]
        if not isinstance(derived_artifact, SnapshotDerivedArtifact):
            return _result(
                False,
                None,
                [
                    _issue(
                        "invalid-derived-artifact",
                        "$.derivedArtifacts[0]",
                        "Package input must be a SnapshotDerivedArtifact.",
                    )
                ],
            )

        issues.extend(_validate_derived_artifact(derived_artifact))
        if issues:
            return _result(False, None, issues)

        if not isinstance(request, ExecutiveIntelligencePackageRequest):
            return _result(False, None, issues)

        return _result(
            True,
            _assemble_package(request, derived_artifact),
            [],
        )


def _validate_request(request: object) -> list[ExecutiveIntelligencePackageIssue]:
    if not isinstance(request, ExecutiveIntelligencePackageRequest):
        return [
            _issue(
                "invalid-package-request",
                "$.request",
                "Package request must be an ExecutiveIntelligencePackageRequest.",
            )
        ]

    issues: list[ExecutiveIntelligencePackageIssue] = []
    if (
        request.package_contract_version
        != EXECUTIVE_INTELLIGENCE_PACKAGE_CONTRACT_VERSION
    ):
        issues.append(
            _issue(
                "unsupported-package-contract-version",
                "$.request.packageContractVersion",
                "Package contract version is not supported.",
            )
        )
    if (
        request.package_assembly_rule_version
        != EXECUTIVE_INTELLIGENCE_PACKAGE_ASSEMBLY_RULE_VERSION
    ):
        issues.append(
            _issue(
                "unsupported-package-assembly-rule",
                "$.request.packageAssemblyRuleVersion",
                "Package assembly rule version is not supported.",
            )
        )
    return issues


def _validate_artifact_count(
    derived_artifacts: tuple[object, ...],
) -> list[ExecutiveIntelligencePackageIssue]:
    if not derived_artifacts:
        return [
            _issue(
                "missing-derived-artifact",
                "$.derivedArtifacts",
                "Package assembly requires exactly one derived artifact.",
            )
        ]
    if len(derived_artifacts) > 1:
        return [
            _issue(
                "multiple-derived-artifacts",
                "$.derivedArtifacts",
                "Package assembly accepts exactly one derived artifact.",
            )
        ]
    return []


def _validate_derived_artifact(
    derived_artifact: SnapshotDerivedArtifact,
) -> list[ExecutiveIntelligencePackageIssue]:
    issues: list[ExecutiveIntelligencePackageIssue] = []
    required_strings = {
        "producer_snapshot_identity": derived_artifact.producer_snapshot_identity,
        "snapshot_contract_version": derived_artifact.snapshot_contract_version,
        "assessment_version": derived_artifact.assessment_version,
        "methodology_version": derived_artifact.methodology_version,
        "derivation_rule_version": derived_artifact.derivation_rule_version,
        "derivation_runtime_version": derived_artifact.derivation_runtime_version,
    }
    for field_name, value in required_strings.items():
        if not isinstance(value, str) or not value.strip():
            issues.append(
                _issue(
                    "incomplete-derived-artifact-lineage",
                    f"$.derivedArtifacts[0].{field_name}",
                    "Derived artifact lineage field is incomplete.",
                )
            )

    if not isinstance(
        derived_artifact.catalog_admission_metadata,
        SnapshotAdmissionMetadata,
    ):
        issues.append(
            _issue(
                "incomplete-derived-artifact-lineage",
                "$.derivedArtifacts[0].catalogAdmissionMetadata",
                "Derived artifact catalog admission metadata is missing.",
            )
        )
    if not isinstance(
        derived_artifact.compatibility_validation_metadata,
        SnapshotCompatibilityValidationMetadata,
    ):
        issues.append(
            _issue(
                "incomplete-derived-artifact-lineage",
                "$.derivedArtifacts[0].compatibilityValidationMetadata",
                "Derived artifact compatibility validation metadata is missing.",
            )
        )
    if not isinstance(derived_artifact.producer_provenance, SnapshotProducerProvenance):
        issues.append(
            _issue(
                "incomplete-derived-artifact-lineage",
                "$.derivedArtifacts[0].producerProvenance",
                "Derived artifact producer provenance is missing.",
            )
        )

    if issues:
        return issues

    issues.extend(_validate_lineage_consistency(derived_artifact))
    return issues


def _validate_lineage_consistency(
    derived_artifact: SnapshotDerivedArtifact,
) -> list[ExecutiveIntelligencePackageIssue]:
    issues: list[ExecutiveIntelligencePackageIssue] = []
    admission_metadata = derived_artifact.catalog_admission_metadata
    compatibility_metadata = derived_artifact.compatibility_validation_metadata
    producer_provenance = derived_artifact.producer_provenance

    checks = (
        (
            derived_artifact.producer_snapshot_identity,
            admission_metadata.producer_snapshot_identity,
            "$.derivedArtifacts[0].catalogAdmissionMetadata.producerSnapshotIdentity",
        ),
        (
            derived_artifact.producer_snapshot_identity,
            producer_provenance.producer_snapshot_identity,
            "$.derivedArtifacts[0].producerProvenance.producerSnapshotIdentity",
        ),
        (
            derived_artifact.snapshot_contract_version,
            compatibility_metadata.snapshot_contract_version,
            "$.derivedArtifacts[0].compatibilityValidationMetadata.snapshotContractVersion",
        ),
        (
            derived_artifact.snapshot_contract_version,
            admission_metadata.response_contract_version,
            "$.derivedArtifacts[0].catalogAdmissionMetadata.responseContractVersion",
        ),
        (
            derived_artifact.assessment_version,
            compatibility_metadata.assessment_version,
            "$.derivedArtifacts[0].compatibilityValidationMetadata.assessmentVersion",
        ),
        (
            derived_artifact.assessment_version,
            admission_metadata.assessment_version,
            "$.derivedArtifacts[0].catalogAdmissionMetadata.assessmentVersion",
        ),
        (
            derived_artifact.methodology_version,
            compatibility_metadata.methodology_version,
            "$.derivedArtifacts[0].compatibilityValidationMetadata.methodologyVersion",
        ),
        (
            derived_artifact.methodology_version,
            admission_metadata.methodology_version,
            "$.derivedArtifacts[0].catalogAdmissionMetadata.methodologyVersion",
        ),
    )
    for left, right, path in checks:
        if left != right:
            issues.append(
                _issue(
                    "inconsistent-derived-artifact-lineage",
                    path,
                    "Derived artifact lineage references are inconsistent.",
                )
            )

    if tuple(admission_metadata.source_component_ids) != tuple(
        producer_provenance.source_component_ids
    ):
        issues.append(
            _issue(
                "inconsistent-derived-artifact-lineage",
                "$.derivedArtifacts[0].producerProvenance.sourceComponentIds",
                "Derived artifact source component lineage is inconsistent.",
            )
        )
    if admission_metadata.production_authority != (
        producer_provenance.production_authority
    ):
        issues.append(
            _issue(
                "inconsistent-derived-artifact-lineage",
                "$.derivedArtifacts[0].producerProvenance.productionAuthority",
                "Derived artifact production authority lineage is inconsistent.",
            )
        )

    return issues


def _assemble_package(
    request: ExecutiveIntelligencePackageRequest,
    derived_artifact: SnapshotDerivedArtifact,
) -> ExecutiveIntelligencePackage:
    lineage = ExecutiveIntelligencePackageLineage(
        producer_snapshot_identity=derived_artifact.producer_snapshot_identity,
        snapshot_contract_version=derived_artifact.snapshot_contract_version,
        assessment_version=derived_artifact.assessment_version,
        methodology_version=derived_artifact.methodology_version,
        derivation_rule_version=derived_artifact.derivation_rule_version,
        derivation_runtime_version=derived_artifact.derivation_runtime_version,
        catalog_admission_metadata=derived_artifact.catalog_admission_metadata,
        producer_provenance=derived_artifact.producer_provenance,
    )
    return ExecutiveIntelligencePackage(
        package_contract_version=request.package_contract_version,
        package_assembly_rule_version=request.package_assembly_rule_version,
        producer_snapshot_identity=derived_artifact.producer_snapshot_identity,
        snapshot_contract_version=derived_artifact.snapshot_contract_version,
        assessment_version=derived_artifact.assessment_version,
        methodology_version=derived_artifact.methodology_version,
        derivation_rule_version=derived_artifact.derivation_rule_version,
        derivation_runtime_version=derived_artifact.derivation_runtime_version,
        lineage=lineage,
        source_derived_artifact=derived_artifact,
    )


def _issue(
    code: str,
    path: str,
    message: str,
) -> ExecutiveIntelligencePackageIssue:
    if code not in EXECUTIVE_INTELLIGENCE_PACKAGE_ISSUE_CODES:
        raise ValueError(f"Undocumented Executive Intelligence Package issue: {code}.")
    return ExecutiveIntelligencePackageIssue(code=code, path=path, message=message)


def _result(
    packaged: bool,
    package: ExecutiveIntelligencePackage | None,
    issues: list[ExecutiveIntelligencePackageIssue],
) -> ExecutiveIntelligencePackageResult:
    return ExecutiveIntelligencePackageResult(
        packaged=packaged,
        package=package,
        issues=tuple(issues),
    )
