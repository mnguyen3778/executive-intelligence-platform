"""Governed admission catalog for compatibility-validated snapshots.

The catalog admits externally produced ExecutiveAssessmentSnapshot artifacts
only after consumer-side compatibility validation succeeds. It preserves
producer-owned snapshot evidence without generating, normalizing, or repairing
producer data.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

from executive_intelligence_platform.snapshot_compatibility import (
    SnapshotCompatibilityIssue,
    validate_snapshot_compatibility,
)


SNAPSHOT_CATALOG_ADMISSION_POLICY_VERSION = "snapshot-catalog-admission-v1"
SNAPSHOT_CATALOG_ISSUE_CODES = MappingProxyType(
    {
        "invalid-producer-snapshot-identity": (
            "Producer snapshot identity is missing or invalid."
        ),
        "incompatible-snapshot": (
            "Snapshot failed compatibility validation and was not admitted."
        ),
        "duplicate-producer-snapshot-identity": (
            "Producer snapshot identity has already been admitted."
        ),
    }
)


@dataclass(frozen=True)
class SnapshotCatalogIssue:
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
class SnapshotAdmissionMetadata:
    producer_snapshot_identity: str
    admission_policy_version: str
    response_contract_version: str
    package_contract_version: str
    assessment_version: str
    methodology_version: str
    source_component_ids: tuple[str, ...]
    production_authority: str
    admission_sequence: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "producerSnapshotIdentity": self.producer_snapshot_identity,
            "admissionPolicyVersion": self.admission_policy_version,
            "responseContractVersion": self.response_contract_version,
            "packageContractVersion": self.package_contract_version,
            "assessmentVersion": self.assessment_version,
            "methodologyVersion": self.methodology_version,
            "sourceComponentIds": list(self.source_component_ids),
            "productionAuthority": self.production_authority,
            "admissionSequence": self.admission_sequence,
        }


@dataclass(frozen=True)
class SnapshotCatalogEntry:
    admission_metadata: SnapshotAdmissionMetadata
    snapshot_evidence: Mapping[str, Any]

    @property
    def producer_snapshot_identity(self) -> str:
        return self.admission_metadata.producer_snapshot_identity

    def to_dict(self) -> dict[str, Any]:
        return {
            "admissionMetadata": self.admission_metadata.to_dict(),
            "snapshotEvidence": _thaw(self.snapshot_evidence),
        }


@dataclass(frozen=True)
class SnapshotAdmissionResult:
    accepted: bool
    entry: SnapshotCatalogEntry | None
    issues: tuple[SnapshotCatalogIssue, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "accepted": self.accepted,
            "entry": self.entry.to_dict() if self.entry is not None else None,
            "issues": [issue.to_dict() for issue in self.issues],
        }


class SnapshotCatalog:
    """Minimal deterministic catalog for admitted snapshot evidence."""

    def __init__(self) -> None:
        self._entries_by_producer_identity: dict[str, SnapshotCatalogEntry] = {}

    def admit(
        self,
        snapshot: object,
        *,
        producer_snapshot_identity: str,
    ) -> SnapshotAdmissionResult:
        compatibility_result = validate_snapshot_compatibility(snapshot)
        issues: list[SnapshotCatalogIssue] = []

        if not compatibility_result.is_valid:
            issues.append(
                _issue(
                    "incompatible-snapshot",
                    "$",
                    "Snapshot failed compatibility validation.",
                )
            )
            issues.extend(
                _compatibility_issue(issue) for issue in compatibility_result.issues
            )

        if not isinstance(producer_snapshot_identity, str) or not (
            producer_snapshot_identity.strip()
        ):
            issues.append(
                _issue(
                    "invalid-producer-snapshot-identity",
                    "$.producerSnapshotIdentity",
                    "Producer snapshot identity must be a non-empty string.",
                )
            )
        elif producer_snapshot_identity in self._entries_by_producer_identity:
            issues.append(
                _issue(
                    "duplicate-producer-snapshot-identity",
                    "$.producerSnapshotIdentity",
                    "Producer snapshot identity has already been admitted.",
                )
            )

        if issues:
            return _result(False, None, issues)

        if not isinstance(snapshot, Mapping):
            return _result(
                False,
                None,
                [
                    _issue(
                        "incompatible-snapshot",
                        "$",
                        "Snapshot failed compatibility validation.",
                    )
                ],
            )

        entry = SnapshotCatalogEntry(
            admission_metadata=_admission_metadata(
                snapshot,
                producer_snapshot_identity=producer_snapshot_identity,
                admission_sequence=len(self._entries_by_producer_identity) + 1,
            ),
            snapshot_evidence=_freeze(snapshot),
        )
        self._entries_by_producer_identity[producer_snapshot_identity] = entry
        return _result(True, entry, [])

    def get(self, producer_snapshot_identity: str) -> SnapshotCatalogEntry | None:
        return self._entries_by_producer_identity.get(producer_snapshot_identity)

    def list_entries(self) -> tuple[SnapshotCatalogEntry, ...]:
        return tuple(
            self._entries_by_producer_identity[producer_snapshot_identity]
            for producer_snapshot_identity in sorted(self._entries_by_producer_identity)
        )


def _admission_metadata(
    snapshot: Mapping[str, Any],
    *,
    producer_snapshot_identity: str,
    admission_sequence: int,
) -> SnapshotAdmissionMetadata:
    package = snapshot["businessDecisionPackage"]
    version_metadata = package["versionMetadata"]
    audit = package["audit"]
    response_status = snapshot["responseStatus"]

    return SnapshotAdmissionMetadata(
        producer_snapshot_identity=producer_snapshot_identity,
        admission_policy_version=SNAPSHOT_CATALOG_ADMISSION_POLICY_VERSION,
        response_contract_version=snapshot["responseContractVersion"],
        package_contract_version=version_metadata["contractVersion"],
        assessment_version=version_metadata["assessmentVersion"],
        methodology_version=version_metadata["methodologyVersion"],
        source_component_ids=tuple(audit["sourceComponentIds"]),
        production_authority=response_status["productionAuthority"],
        admission_sequence=admission_sequence,
    )


def _issue(code: str, path: str, message: str) -> SnapshotCatalogIssue:
    if code not in SNAPSHOT_CATALOG_ISSUE_CODES:
        raise ValueError(f"Undocumented snapshot catalog issue code: {code}.")
    return SnapshotCatalogIssue(code=code, path=path, message=message)


def _compatibility_issue(issue: SnapshotCompatibilityIssue) -> SnapshotCatalogIssue:
    return SnapshotCatalogIssue(
        code=issue.code,
        path=issue.path,
        message=issue.message,
    )


def _result(
    accepted: bool,
    entry: SnapshotCatalogEntry | None,
    issues: list[SnapshotCatalogIssue],
) -> SnapshotAdmissionResult:
    return SnapshotAdmissionResult(
        accepted=accepted,
        entry=entry,
        issues=tuple(issues),
    )


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(value[key]) for key in value})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, tuple):
        return tuple(_freeze(item) for item in value)
    return value


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw(value[key]) for key in value}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return value
