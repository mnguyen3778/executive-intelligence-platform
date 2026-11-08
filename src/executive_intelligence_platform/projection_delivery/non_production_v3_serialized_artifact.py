"""Exact, non-releasable synthetic v3 delivery artifact identity and bytes."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from hashlib import sha256

from executive_intelligence_platform.snapshot_compatibility.compatibility import (
    GOVERNED_ASSESSMENT_VERSION, SUPPORTED_METHODOLOGY_VERSION,
    SUPPORTED_RESPONSE_CONTRACT_VERSION,
)
from .recommendation_action_explain_delivery import (
    RECOMMENDATION_ACTION_EXPLAIN_DELIVERY_CONTRACT_VERSION as DELIVERY_VERSION,
    InternalRecommendationActionExplainDeliveryCandidate,
    prepare_recommendation_action_explain_delivery,
)
from .verified_admission import (
    LOCAL_V3_PACKAGE_VERSION, VerifiedAdmissionError, VerifiedSnapshotGateway,
)


SERIALIZATION_PROFILE_VERSION = "eip-synthetic-v3-artifact-json-v1"
DECISION_TABLE_VERSION = "recommendation-decision-table-set-v1"
FIELD_SCOPE = ("recommendationActionText",)
_DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z", re.ASCII)


def _identifier(value: object) -> bool:
    return (type(value) is str and bool(value) and value.isascii() and
            value == value.strip() and
            all(32 <= ord(char) <= 126 for char in value))


def _instance_id(value: object) -> bool:
    # The former projection-derived name and a digest are not assigned IDs.
    return (_identifier(value) and
            not value.startswith(("synthetic-v3-artifact:", "sha256:")))


def _scalar_string(value: object) -> bool:
    if type(value) is not str:
        return False
    try:
        value.encode("utf-8", "strict")
    except UnicodeEncodeError:
        return False
    return True


@dataclass(frozen=True, slots=True)
class SyntheticV3ArtifactScope:
    """Fixture-held EIP scope; applicability is independent of envelope claims."""

    business_entity_id: str
    environment_id: str
    engagement_id: str | None
    engagement_applies: bool


@dataclass(frozen=True, slots=True)
class SyntheticV3SerializedArtifact:
    artifact_instance_id: str
    serialized_bytes: bytes
    integrity_reference: str
    release_eligible: bool = field(default=False, init=False)


def _scope_valid(scope: object) -> bool:
    return (type(scope) is SyntheticV3ArtifactScope and
            _identifier(scope.business_entity_id) and
            _identifier(scope.environment_id) and
            type(scope.engagement_applies) is bool and
            (_identifier(scope.engagement_id) if scope.engagement_applies
             else scope.engagement_id is None))


def _fresh(candidate: object, gateway: object, admission: object):
    if (type(candidate) is not InternalRecommendationActionExplainDeliveryCandidate or
            candidate.release_eligible is not False or
            type(gateway) is not VerifiedSnapshotGateway):
        raise VerifiedAdmissionError("invalid-v3-candidate")
    fresh = prepare_recommendation_action_explain_delivery(
        gateway, admission, package_contract_version=LOCAL_V3_PACKAGE_VERSION,
        delivery_contract_version=DELIVERY_VERSION)
    if candidate != fresh or fresh.verified_projection.release_eligible is not False:
        raise VerifiedAdmissionError("invalid-v3-candidate")
    projection = fresh.verified_projection
    if (projection.package_contract_version != LOCAL_V3_PACKAGE_VERSION or
            projection.methodology_version != SUPPORTED_METHODOLOGY_VERSION or
            projection.producer_snapshot_identity !=
            projection.verification_evidence.producer_snapshot_identity or
            not _identifier(projection.producer_snapshot_identity) or
            not projection.recommendations or
            any(row.recommendation_decision_table_version != DECISION_TABLE_VERSION
                or not _scalar_string(row.recommendation_action_text)
                for row in projection.recommendations)):
        raise VerifiedAdmissionError("invalid-v3-candidate")
    return fresh


def _envelope(candidate, artifact_instance_id: str, scope: SyntheticV3ArtifactScope):
    return {
        "artifactInstanceId": artifact_instance_id,
        "artifactScope": {
            "businessEntityId": scope.business_entity_id,
            "engagementId": scope.engagement_id,
            "environmentId": scope.environment_id,
        },
        "content": candidate.content.to_dict(),
        "deliveryContractVersion": DELIVERY_VERSION,
        "fieldScope": list(FIELD_SCOPE),
        "producerLineage": {
            "producerSnapshotIdentity": candidate.verified_projection.producer_snapshot_identity,
        },
        "serializationProfileVersion": SERIALIZATION_PROFILE_VERSION,
        "versionContext": {
            "assessmentVersion": GOVERNED_ASSESSMENT_VERSION,
            "methodologyVersion": SUPPORTED_METHODOLOGY_VERSION,
            "packageContractVersion": LOCAL_V3_PACKAGE_VERSION,
            "recommendationDecisionTableVersion": DECISION_TABLE_VERSION,
            "snapshotResponseContractVersion": SUPPORTED_RESPONSE_CONTRACT_VERSION,
        },
    }


def _encode(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=True, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def _no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate-key")
        result[key] = value
    return result


def _no_numbers(_value):
    raise ValueError("numeric-value")


def _parse(data: bytes):
    text = data.decode("utf-8", "strict")
    if text.startswith("\ufeff"):
        raise ValueError("byte-order-mark")
    return json.loads(text, object_pairs_hook=_no_duplicates,
                      parse_int=_no_numbers, parse_float=_no_numbers,
                      parse_constant=_no_numbers)


def create_synthetic_v3_artifact(
    candidate: object, gateway: object, admission: object, *,
    artifact_instance_id: object, trusted_scope: object,
) -> SyntheticV3SerializedArtifact:
    """Bind a fixture-assigned instance ID to freshly verified producer content."""
    if (not _instance_id(artifact_instance_id) or not _scope_valid(trusted_scope)):
        raise VerifiedAdmissionError("invalid-synthetic-artifact-identity-or-scope")
    fresh = _fresh(candidate, gateway, admission)
    if artifact_instance_id == fresh.verified_projection.producer_snapshot_identity:
        raise VerifiedAdmissionError("invalid-synthetic-artifact-identity-or-scope")
    data = _encode(_envelope(fresh, artifact_instance_id, trusted_scope))
    return SyntheticV3SerializedArtifact(
        artifact_instance_id, data, "sha256:" + sha256(data).hexdigest())


def verify_synthetic_v3_artifact(
    artifact: object, candidate: object, gateway: object, admission: object, *,
    expected_artifact_instance_id: object, trusted_scope: object,
) -> bool:
    """Verify exact fixture-held scope, candidate, canonical bytes, and digest.

    Returns only a boolean, never content or an authorization decision.
    """
    try:
        if (type(artifact) is not SyntheticV3SerializedArtifact or
                artifact.release_eligible is not False or
                not _instance_id(expected_artifact_instance_id) or
                artifact.artifact_instance_id != expected_artifact_instance_id or
                not _scope_valid(trusted_scope) or
                type(artifact.serialized_bytes) is not bytes or
                type(artifact.integrity_reference) is not str or
                _DIGEST.fullmatch(artifact.integrity_reference) is None):
            return False
        fresh = _fresh(candidate, gateway, admission)
        if artifact.artifact_instance_id == fresh.verified_projection.producer_snapshot_identity:
            return False
        parsed = _parse(artifact.serialized_bytes)
        expected = _envelope(fresh, expected_artifact_instance_id, trusted_scope)
        if (parsed != expected or
                _encode(parsed) != artifact.serialized_bytes or
                artifact.integrity_reference !=
                "sha256:" + sha256(artifact.serialized_bytes).hexdigest()):
            return False
        return True
    except (VerifiedAdmissionError, ValueError, TypeError, AttributeError,
            UnicodeError, KeyError, OverflowError):
        return False
