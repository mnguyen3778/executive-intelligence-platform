"""Synthetic v3 publication proof only; never publication or release authority.

The local harness retains ``trusted_fixture`` independently of presented evidence.
Equality with that fixture is a deterministic tamper check, not an authenticity
protocol. No live source, publication mutation, or client serializer exists here.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from hashlib import sha256

from .recommendation_action_explain_delivery import (
    RECOMMENDATION_ACTION_EXPLAIN_DELIVERY_CONTRACT_VERSION,
    InternalRecommendationActionExplainDeliveryCandidate,
    prepare_recommendation_action_explain_delivery,
)
from .verified_admission import (
    LOCAL_V3_PACKAGE_VERSION, VerificationEvidence, VerifiedAdmissionError,
    VerifiedSnapshotGateway,
)
from executive_intelligence_platform.snapshot_compatibility.compatibility import (
    SUPPORTED_METHODOLOGY_VERSION,
)
from executive_intelligence_platform.snapshot_derivation.local_v3_recommendation_projection import (
    LocalV3RecommendationProjection,
)


APPROVED_FIELD_SCOPE = ("recommendationActionText",)
RECOMMENDATION_DECISION_TABLE_VERSION = "recommendation-decision-table-set-v1"


@dataclass(frozen=True, slots=True)
class SyntheticV3PublicationRecord:
    """Historical fixture record; its presence says nothing about currentness."""

    artifact_identity: str
    artifact_integrity_reference: str
    occurrence: str
    revision: str
    series: str
    producer_snapshot_identity: str
    verification_evidence: VerificationEvidence
    package_version: str
    methodology_version: str
    decision_table_version: str
    field_scope: tuple[str, ...]
    delivery_contract_version: str


@dataclass(frozen=True, slots=True)
class SyntheticV3CurrentState:
    occurrence: str
    revision: str
    state: str  # current, withdrawn, superseded, revoked, invalidated
    superseded_by: str | None = None


@dataclass(frozen=True, slots=True)
class SyntheticV3AuthoritySnapshot:
    generation: str
    available: bool
    records: tuple[SyntheticV3PublicationRecord, ...]
    current_states: tuple[SyntheticV3CurrentState, ...]


@dataclass(frozen=True, slots=True)
class SyntheticV3Selector:
    artifact_identity: str
    occurrence: str
    revision: str
    observed_generation: str


@dataclass(frozen=True, slots=True)
class SyntheticV3VerifiedIdentity:
    artifact_identity: str
    artifact_integrity_reference: str
    occurrence: str
    revision: str
    authority_generation: str


@dataclass(frozen=True, slots=True)
class SyntheticV3VerificationResult:
    status: str
    reason: str | None = None
    evidence: SyntheticV3VerifiedIdentity | None = None
    release_eligible: bool = field(default=False, init=False)


def _reject(reason: str) -> SyntheticV3VerificationResult:
    return SyntheticV3VerificationResult("SYNTHETIC_REJECTED", reason)


def _name(value: object) -> bool:
    return type(value) is str and bool(value.strip())


def _integrity(candidate: InternalRecommendationActionExplainDeliveryCandidate) -> str:
    """Digest the trusted internal projection, including producer lineage."""
    data = {
        "deliveryContractVersion": candidate.delivery_contract_version,
        "verifiedProjection": asdict(candidate.verified_projection),
    }
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=False).encode("utf-8")
    return "sha256:" + sha256(canonical).hexdigest()


def synthetic_v3_artifact_identity(
    candidate: InternalRecommendationActionExplainDeliveryCandidate,
) -> str:
    """Deterministic local artifact name, independent of publication occurrence."""
    return "synthetic-v3-artifact:" + _integrity(candidate)[7:]


def verify_synthetic_v3_publication(
    selector: object,
    candidate: object,
    authority: object,
    *,
    trusted_fixture: object,
    gateway: object,
    admission: object,
) -> SyntheticV3VerificationResult:
    """Check one fixture-held current state; a PASS never authorizes delivery."""
    if (type(selector) is not SyntheticV3Selector or
            not all(_name(v) for v in (
                selector.artifact_identity, selector.occurrence, selector.revision,
                selector.observed_generation))):
        return _reject("malformed-evidence")
    if (type(candidate) is not InternalRecommendationActionExplainDeliveryCandidate or
            candidate.release_eligible is not False or
            type(candidate.verified_projection) is not LocalV3RecommendationProjection or
            candidate.verified_projection.release_eligible is not False or
            type(gateway) is not VerifiedSnapshotGateway):
        return _reject("invalid-v3-candidate")
    if type(trusted_fixture) is not SyntheticV3AuthoritySnapshot:
        return _reject("synthetic-fixture-missing")
    if type(authority) is not SyntheticV3AuthoritySnapshot:
        return _reject("publication-evidence-missing")
    if (not _name(authority.generation) or type(authority.available) is not bool or
            type(authority.records) is not tuple or
            type(authority.current_states) is not tuple or
            not _name(trusted_fixture.generation) or
            type(trusted_fixture.available) is not bool or
            type(trusted_fixture.records) is not tuple or
            type(trusted_fixture.current_states) is not tuple):
        return _reject("malformed-evidence")
    if not authority.available or not trusted_fixture.available:
        return _reject("publication-evidence-unavailable")
    if authority != trusted_fixture:
        return _reject("synthetic-fixture-mismatch")
    if selector.observed_generation != authority.generation:
        return _reject("stale-publication-evidence")

    records: dict[str, SyntheticV3PublicationRecord] = {}
    revisions: set[tuple[str, str]] = set()
    for record in authority.records:
        if (type(record) is not SyntheticV3PublicationRecord or
                not all(_name(v) for v in (
                    record.artifact_identity, record.artifact_integrity_reference,
                    record.occurrence, record.revision, record.series,
                    record.producer_snapshot_identity, record.package_version,
                    record.methodology_version, record.decision_table_version,
                    record.delivery_contract_version)) or
                type(record.verification_evidence) is not VerificationEvidence or
                type(record.field_scope) is not tuple or
                not all(_name(v) for v in record.field_scope)):
            return _reject("malformed-evidence")
        if record.occurrence in records or (record.series, record.revision) in revisions:
            return _reject("conflicting-publication-records")
        records[record.occurrence] = record
        revisions.add((record.series, record.revision))

    states: dict[str, SyntheticV3CurrentState] = {}
    current_series: set[str] = set()
    for state in authority.current_states:
        if (type(state) is not SyntheticV3CurrentState or
                not _name(state.occurrence) or not _name(state.revision) or
                state.state not in ("current", "withdrawn", "superseded",
                                    "revoked", "invalidated") or
                (state.superseded_by is not None and
                 not _name(state.superseded_by)) or
                (state.state == "superseded") !=
                (state.superseded_by is not None)):
            return _reject("malformed-evidence")
        record = records.get(state.occurrence)
        if (record is None or record.revision != state.revision or
                state.occurrence in states):
            return _reject("conflicting-current-state")
        if (state.state == "superseded" and
                (state.superseded_by == state.occurrence or
                 state.superseded_by not in records or
                 records[state.superseded_by].series != record.series)):
            return _reject("conflicting-current-state")
        if state.state == "current":
            if record.series in current_series:
                return _reject("ambiguous-current-revision")
            current_series.add(record.series)
        states[state.occurrence] = state
    if set(states) != set(records):
        return _reject("missing-current-state")

    record = records.get(selector.occurrence)
    if record is None:
        return _reject("publication-record-missing")
    if selector.revision != record.revision:
        return _reject("revision-identity-mismatch")
    if selector.artifact_identity != record.artifact_identity:
        return _reject("artifact-identity-mismatch")
    state = states[record.occurrence]
    if state.state != "current":
        return _reject("publication-" + state.state)

    try:
        fresh = prepare_recommendation_action_explain_delivery(
            gateway, admission, package_contract_version=LOCAL_V3_PACKAGE_VERSION,
            delivery_contract_version=
            RECOMMENDATION_ACTION_EXPLAIN_DELIVERY_CONTRACT_VERSION,
        )
        if candidate != fresh:
            return _reject("invalid-v3-candidate")
        projection = fresh.verified_projection
        if (fresh.delivery_contract_version !=
                RECOMMENDATION_ACTION_EXPLAIN_DELIVERY_CONTRACT_VERSION or
                projection.package_contract_version != LOCAL_V3_PACKAGE_VERSION or
                projection.methodology_version != SUPPORTED_METHODOLOGY_VERSION or
                not projection.recommendations or
                any(row.recommendation_decision_table_version !=
                    RECOMMENDATION_DECISION_TABLE_VERSION
                    for row in projection.recommendations)):
            return _reject("invalid-v3-candidate")
        integrity = _integrity(fresh)
        identity = synthetic_v3_artifact_identity(fresh)
    except (VerifiedAdmissionError, TypeError, ValueError, AttributeError, KeyError):
        return _reject("invalid-v3-candidate")

    if record.artifact_identity != identity:
        return _reject("artifact-identity-mismatch")
    if record.artifact_integrity_reference != integrity:
        return _reject("artifact-integrity-mismatch")
    if (record.producer_snapshot_identity != projection.producer_snapshot_identity or
            record.producer_snapshot_identity !=
            projection.verification_evidence.producer_snapshot_identity or
            record.verification_evidence != projection.verification_evidence):
        return _reject("producer-lineage-mismatch")
    if (record.package_version != LOCAL_V3_PACKAGE_VERSION or
            record.methodology_version != projection.methodology_version or
            record.decision_table_version !=
            RECOMMENDATION_DECISION_TABLE_VERSION or
            record.field_scope != APPROVED_FIELD_SCOPE or
            record.delivery_contract_version != fresh.delivery_contract_version):
        return _reject("v3-contract-mismatch")
    return SyntheticV3VerificationResult(
        "SYNTHETIC_ACCEPTED",
        evidence=SyntheticV3VerifiedIdentity(identity, integrity, record.occurrence,
                                             record.revision, authority.generation),
    )
