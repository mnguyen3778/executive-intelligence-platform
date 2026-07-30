"""Deterministic derivation runtime for admitted snapshot catalog entries.

The runtime consumes only SnapshotCatalogEntry instances. It produces
platform-owned lineage artifacts without modifying catalog entries, inspecting
assessment content for conclusions, or recomputing Assessment Service outputs.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from executive_intelligence_platform.snapshot_catalog import (
    SnapshotAdmissionMetadata,
    SnapshotCatalogEntry,
)


SNAPSHOT_DERIVATION_RULE_VERSION = "snapshot-derivation-lineage-artifact-v1"
SNAPSHOT_DERIVATION_RUNTIME_VERSION = "snapshot-derivation-runtime-v1"
SNAPSHOT_DERIVATION_ISSUE_CODES = MappingProxyType(
    {
        "invalid-catalog-entry": (
            "Derivation input is not an admitted snapshot catalog entry."
        ),
        "invalid-derivation-request": (
            "Derivation request is missing or invalid."
        ),
        "unsupported-derivation-rule": (
            "Requested derivation rule is not supported."
        ),
        "incomplete-catalog-lineage": (
            "Catalog admission metadata is incomplete for derivation lineage."
        ),
        "missing-snapshot-evidence": (
            "Catalog entry does not contain preserved snapshot evidence."
        ),
    }
)


@dataclass(frozen=True)
class SnapshotDerivationIssue:
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
class SnapshotDerivationRequest:
    derivation_rule_version: str = SNAPSHOT_DERIVATION_RULE_VERSION

    def to_dict(self) -> dict[str, str]:
        return {
            "derivationRuleVersion": self.derivation_rule_version,
        }


@dataclass(frozen=True)
class SnapshotCompatibilityValidationMetadata:
    snapshot_contract_version: str
    assessment_version: str
    methodology_version: str

    def to_dict(self) -> dict[str, str]:
        return {
            "snapshotContractVersion": self.snapshot_contract_version,
            "assessmentVersion": self.assessment_version,
            "methodologyVersion": self.methodology_version,
        }


@dataclass(frozen=True)
class SnapshotProducerProvenance:
    producer_snapshot_identity: str
    source_component_ids: tuple[str, ...]
    production_authority: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "producerSnapshotIdentity": self.producer_snapshot_identity,
            "sourceComponentIds": list(self.source_component_ids),
            "productionAuthority": self.production_authority,
        }


@dataclass(frozen=True)
class SnapshotDerivedArtifact:
    producer_snapshot_identity: str
    snapshot_contract_version: str
    assessment_version: str
    methodology_version: str
    catalog_admission_metadata: SnapshotAdmissionMetadata
    compatibility_validation_metadata: SnapshotCompatibilityValidationMetadata
    producer_provenance: SnapshotProducerProvenance
    derivation_rule_version: str
    derivation_runtime_version: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "producerSnapshotIdentity": self.producer_snapshot_identity,
            "snapshotContractVersion": self.snapshot_contract_version,
            "assessmentVersion": self.assessment_version,
            "methodologyVersion": self.methodology_version,
            "catalogAdmissionMetadata": (
                self.catalog_admission_metadata.to_dict()
            ),
            "compatibilityValidationMetadata": (
                self.compatibility_validation_metadata.to_dict()
            ),
            "producerProvenance": self.producer_provenance.to_dict(),
            "derivationRuleVersion": self.derivation_rule_version,
            "derivationRuntimeVersion": self.derivation_runtime_version,
        }


@dataclass(frozen=True)
class SnapshotDerivationResult:
    derived: bool
    artifact: SnapshotDerivedArtifact | None
    issues: tuple[SnapshotDerivationIssue, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "derived": self.derived,
            "artifact": self.artifact.to_dict() if self.artifact is not None else None,
            "issues": [issue.to_dict() for issue in self.issues],
        }


class SnapshotDerivationRuntime:
    """Minimal deterministic runtime over admitted catalog entries."""

    def derive(
        self,
        catalog_entry: object,
        request: object,
    ) -> SnapshotDerivationResult:
        issues: list[SnapshotDerivationIssue] = []

        if not isinstance(request, SnapshotDerivationRequest):
            issues.append(
                _issue(
                    "invalid-derivation-request",
                    "$.request",
                    "Derivation request must be a SnapshotDerivationRequest.",
                )
            )
        elif request.derivation_rule_version != SNAPSHOT_DERIVATION_RULE_VERSION:
            issues.append(
                _issue(
                    "unsupported-derivation-rule",
                    "$.request.derivationRuleVersion",
                    "Derivation rule version is not supported.",
                )
            )

        if not isinstance(catalog_entry, SnapshotCatalogEntry):
            issues.append(
                _issue(
                    "invalid-catalog-entry",
                    "$.catalogEntry",
                    "Derivation requires an admitted SnapshotCatalogEntry.",
                )
            )
            return _result(False, None, issues)

        issues.extend(_validate_catalog_entry(catalog_entry))
        if issues:
            return _result(False, None, issues)

        if not isinstance(request, SnapshotDerivationRequest):
            return _result(False, None, issues)

        artifact = _derive_artifact(catalog_entry, request)
        return _result(True, artifact, [])


def _validate_catalog_entry(
    catalog_entry: SnapshotCatalogEntry,
) -> list[SnapshotDerivationIssue]:
    issues: list[SnapshotDerivationIssue] = []
    metadata = catalog_entry.admission_metadata

    required_metadata = {
        "producer_snapshot_identity": metadata.producer_snapshot_identity,
        "admission_policy_version": metadata.admission_policy_version,
        "response_contract_version": metadata.response_contract_version,
        "assessment_version": metadata.assessment_version,
        "methodology_version": metadata.methodology_version,
        "production_authority": metadata.production_authority,
    }
    for field_name, value in required_metadata.items():
        if not isinstance(value, str) or not value.strip():
            issues.append(
                _issue(
                    "incomplete-catalog-lineage",
                    f"$.catalogEntry.admissionMetadata.{field_name}",
                    "Catalog admission metadata is incomplete.",
                )
            )

    if not metadata.source_component_ids:
        issues.append(
            _issue(
                "incomplete-catalog-lineage",
                "$.catalogEntry.admissionMetadata.source_component_ids",
                "Catalog admission source component lineage is incomplete.",
            )
        )
    if not isinstance(catalog_entry.snapshot_evidence, MappingProxyType):
        issues.append(
            _issue(
                "missing-snapshot-evidence",
                "$.catalogEntry.snapshotEvidence",
                "Catalog entry must contain preserved immutable snapshot evidence.",
            )
        )

    return issues


def _derive_artifact(
    catalog_entry: SnapshotCatalogEntry,
    request: SnapshotDerivationRequest,
) -> SnapshotDerivedArtifact:
    metadata = catalog_entry.admission_metadata
    compatibility_metadata = SnapshotCompatibilityValidationMetadata(
        snapshot_contract_version=metadata.response_contract_version,
        assessment_version=metadata.assessment_version,
        methodology_version=metadata.methodology_version,
    )
    producer_provenance = SnapshotProducerProvenance(
        producer_snapshot_identity=metadata.producer_snapshot_identity,
        source_component_ids=tuple(metadata.source_component_ids),
        production_authority=metadata.production_authority,
    )

    return SnapshotDerivedArtifact(
        producer_snapshot_identity=metadata.producer_snapshot_identity,
        snapshot_contract_version=metadata.response_contract_version,
        assessment_version=metadata.assessment_version,
        methodology_version=metadata.methodology_version,
        catalog_admission_metadata=metadata,
        compatibility_validation_metadata=compatibility_metadata,
        producer_provenance=producer_provenance,
        derivation_rule_version=request.derivation_rule_version,
        derivation_runtime_version=SNAPSHOT_DERIVATION_RUNTIME_VERSION,
    )


def _issue(code: str, path: str, message: str) -> SnapshotDerivationIssue:
    if code not in SNAPSHOT_DERIVATION_ISSUE_CODES:
        raise ValueError(f"Undocumented snapshot derivation issue code: {code}.")
    return SnapshotDerivationIssue(code=code, path=path, message=message)


def _result(
    derived: bool,
    artifact: SnapshotDerivedArtifact | None,
    issues: list[SnapshotDerivationIssue],
) -> SnapshotDerivationResult:
    return SnapshotDerivationResult(
        derived=derived,
        artifact=artifact,
        issues=tuple(issues),
    )
