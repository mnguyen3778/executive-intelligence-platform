"""NON-PRODUCTION. SYNTHETIC EVIDENCE ONLY. NOT A PUBLICATION AUTHORITY SOURCE.

Local fixture custody supplies a complete, immutable EIP state snapshot. A
caller selector cannot create a publication, revision, or current-state fact.
This module is deliberately absent from the production delivery entry points.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256

from .delivery import (
    WEBSITE_PROJECTION_DELIVERY_CONTRACT_VERSION,
    WEBSITE_PROJECTION_DELIVERY_PUBLICATION_POLICY_VERSION,
    WebsiteProjectionDeliveryContractInstance,
)
from .verified_admission import (
    VerificationEvidence,
    VerifiedAdmissionError,
    VerifiedSnapshotAdmission,
    VerifiedSnapshotGateway,
)


@dataclass(frozen=True)
class SyntheticPublicationRecord:
    occurrence: str
    revision: str
    series: str
    artifact_bytes: bytes
    content_sha256: str
    contract_version: str
    policy_version: str
    producer_snapshot_identity: str
    verification_evidence: VerificationEvidence
    state: str  # current, unpublished, superseded, withdrawn
    eligible: bool
    superseded_by: str | None = None


@dataclass(frozen=True)
class SyntheticAuthoritySnapshot:
    """One trusted local fixture view; generation is a concurrency fence."""

    generation: str
    available: bool
    records: tuple[SyntheticPublicationRecord, ...]


@dataclass(frozen=True)
class PublicationSelector:
    """Untrusted requested identity and observed authority generation."""

    occurrence: str
    revision: str
    observed_generation: str


@dataclass(frozen=True)
class VerifiedPublication:
    occurrence: str
    revision: str
    series: str
    content_sha256: str
    contract_version: str
    policy_version: str
    producer_snapshot_identity: str
    verification_evidence: VerificationEvidence
    authority_generation: str


@dataclass(frozen=True)
class PublicationVerificationResult:
    status: str
    reason: str | None = None
    evidence: VerifiedPublication | None = None


def _reject(reason: str) -> PublicationVerificationResult:
    return PublicationVerificationResult("NOT_ACCEPTED", reason)


def _name(value: object) -> bool:
    return type(value) is str and bool(value.strip())


def verify_publication(
    selector: object,
    artifact_bytes: object,
    authority: object,
    *,
    admission: object,
    gateway: object,
) -> PublicationVerificationResult:
    """Verify one exact occurrence against one synthetic authority snapshot.

    The harness, not the artifact holder, has custody of ``authority``,
    ``admission``, and ``gateway``. This is an in-memory proof, not a trust
    protocol or Resource-specific selection decision.
    """
    if (type(selector) is not PublicationSelector or
            not _name(selector.occurrence) or not _name(selector.revision) or
            not _name(selector.observed_generation) or
            type(artifact_bytes) is not bytes):
        return _reject("malformed-evidence")
    if type(authority) is not SyntheticAuthoritySnapshot:
        return _reject("publication-evidence-missing")
    if (not _name(authority.generation) or type(authority.available) is not bool or
            type(authority.records) is not tuple):
        return _reject("malformed-evidence")
    if not authority.available:
        return _reject("publication-evidence-unavailable")
    if selector.observed_generation != authority.generation:
        return _reject("stale-publication-evidence")
    if (type(admission) is not VerifiedSnapshotAdmission or
            type(gateway) is not VerifiedSnapshotGateway):
        return _reject("verified-admission-missing")

    # Reject contradictory fixture state before choosing any requested record.
    occurrences: set[str] = set()
    revisions: dict[tuple[str, str], tuple[str, str, str]] = {}
    current: dict[str, str] = {}
    for record in authority.records:
        if (type(record) is not SyntheticPublicationRecord or
                not all(_name(value) for value in (
                    record.occurrence, record.revision, record.series,
                    record.content_sha256, record.contract_version,
                    record.policy_version, record.producer_snapshot_identity,
                )) or type(record.artifact_bytes) is not bytes or
                type(record.verification_evidence) is not VerificationEvidence or
                type(record.eligible) is not bool or
                record.state not in ("current", "unpublished", "superseded", "withdrawn") or
                (record.superseded_by is not None and not _name(record.superseded_by))):
            return _reject("malformed-evidence")
        if record.occurrence in occurrences:
            return _reject("conflicting-publication-identity")
        occurrences.add(record.occurrence)
        revision_key = (record.series, record.revision)
        revision_value = (record.occurrence, record.content_sha256,
                          record.producer_snapshot_identity)
        if revision_key in revisions and revisions[revision_key] != revision_value:
            return _reject("conflicting-revision-state")
        revisions[revision_key] = revision_value
        if record.state == "current":
            if record.series in current and current[record.series] != record.revision:
                return _reject("conflicting-current-revisions")
            current[record.series] = record.revision

    matching = tuple(r for r in authority.records if r.occurrence == selector.occurrence)
    if not matching:
        return _reject("publication-identity-mismatch")
    record = matching[0]
    if record.revision != selector.revision:
        return _reject("revision-identity-mismatch")
    if record.state == "withdrawn":
        return _reject("publication-withdrawn")
    if record.state == "superseded" or record.superseded_by is not None:
        return _reject("publication-superseded")
    if record.state != "current" or not record.eligible:
        return _reject("publication-ineligible")
    if record.contract_version != WEBSITE_PROJECTION_DELIVERY_CONTRACT_VERSION:
        return _reject("contract-version-unsupported")
    if record.policy_version != WEBSITE_PROJECTION_DELIVERY_PUBLICATION_POLICY_VERSION:
        return _reject("publication-policy-mismatch")
    if artifact_bytes != record.artifact_bytes:
        return _reject("artifact-bytes-mismatch")
    if sha256(artifact_bytes).hexdigest() != record.content_sha256:
        return _reject("content-identity-mismatch")

    try:
        delivered = gateway.deliver(admission)
        delivery = delivered.delivery.delivery
        if delivery is None or not delivered.delivery.delivered:
            return _reject("publication-ineligible")
        expected = WebsiteProjectionDeliveryContractInstance(delivery)
        serialized = expected.serialize().encode("utf-8")
        if serialized != artifact_bytes:
            return _reject("artifact-bytes-mismatch")
        if (record.verification_evidence != delivered.evidence or
                record.producer_snapshot_identity != delivered.evidence.producer_snapshot_identity or
                delivery.projection_reference.producer_snapshot_identity !=
                record.producer_snapshot_identity or
                delivery.lineage.producer_snapshot_identity !=
                record.producer_snapshot_identity):
            return _reject("producer-lineage-mismatch")
        if (expected.delivery_contract_version != record.contract_version or
                delivery.version_context.delivery_contract_version != record.contract_version or
                delivery.lineage.delivery_contract_version != record.contract_version):
            return _reject("contract-version-unsupported")
        if (expected.publication_policy_version != record.policy_version or
                delivery.version_context.publication_policy_version != record.policy_version or
                delivery.lineage.publication_policy_version != record.policy_version):
            return _reject("publication-policy-mismatch")
    except (VerifiedAdmissionError, TypeError, ValueError, AttributeError, KeyError):
        return _reject("verified-admission-invalid")

    return PublicationVerificationResult(
        "ACCEPTED", evidence=VerifiedPublication(
            record.occurrence, record.revision, record.series,
            record.content_sha256, record.contract_version, record.policy_version,
            record.producer_snapshot_identity, delivered.evidence, authority.generation,
        ),
    )
