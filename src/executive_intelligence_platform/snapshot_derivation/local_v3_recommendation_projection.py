"""Internal, non-releasable projection of verified local v3 recommendations.

This module is not a publisher, authorization source, or production route.
Only the owner-configured gateway can supply the signed local delivery used here.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from executive_intelligence_platform.projection_delivery.verified_admission import (
    LOCAL_V3_PACKAGE_VERSION,
    LocalV3GovernedDelivery,
    VerificationEvidence,
    VerifiedAdmissionError,
    VerifiedSnapshotGateway,
)
from executive_intelligence_platform.snapshot_compatibility.compatibility import (
    SUPPORTED_METHODOLOGY_VERSION,
)


@dataclass(frozen=True)
class LocalV3Recommendation:
    finding_id: str | None
    recommendation_classification: str
    recommendation_decision_identifier: str
    recommendation_decision_table_version: str
    recommendation_action_text: str


@dataclass(frozen=True)
class LocalV3RecommendationProjection:
    """Internal evidence only; no display serialization or release authority."""

    recommendations: tuple[LocalV3Recommendation, ...]
    package_contract_version: str
    methodology_version: str
    producer_snapshot_identity: str
    verification_evidence: VerificationEvidence
    release_eligible: bool = field(default=False, init=False)


def project_local_v3_recommendations(
    gateway: object, admission: object, *, package_contract_version: str,
) -> LocalV3RecommendationProjection:
    """Project only content freshly delivered by the selected trusted gateway."""
    if type(gateway) is not VerifiedSnapshotGateway:
        raise VerifiedAdmissionError("untrusted-local-v3-gateway")

    # This call enforces explicit selection and same-gateway admission, then
    # independently reverifies the original signed bytes and sidecar.
    delivered = gateway.deliver_local_v3(
        admission, package_contract_version=package_contract_version,
    )
    if type(delivered) is not LocalV3GovernedDelivery:
        raise VerifiedAdmissionError("invalid-local-v3-delivery")

    try:
        snapshot = json.loads(delivered._snapshot_bytes)
        metadata = snapshot["businessDecisionPackage"]["versionMetadata"]
        rows = delivered.governed_conclusions["recommendations"]
        if (metadata["contractVersion"] != LOCAL_V3_PACKAGE_VERSION or
                metadata["methodologyVersion"] != SUPPORTED_METHODOLOGY_VERSION or
                not rows or type(delivered.evidence) is not VerificationEvidence or
                not delivered.evidence.producer_snapshot_identity):
            raise ValueError("Incomplete verified local v3 content")
        recommendations = tuple(
            LocalV3Recommendation(
                finding_id=row["findingId"],
                recommendation_classification=row["recommendationClassification"],
                recommendation_decision_identifier=row["recommendationDecisionIdentifier"],
                recommendation_decision_table_version=row["recommendationDecisionTableVersion"],
                recommendation_action_text=row["recommendationActionText"],
            )
            for row in rows
        )
    except (TypeError, ValueError, KeyError, IndexError, AttributeError):
        raise VerifiedAdmissionError("invalid-local-v3-projection-source") from None

    return LocalV3RecommendationProjection(
        recommendations=recommendations,
        package_contract_version=metadata["contractVersion"],
        methodology_version=metadata["methodologyVersion"],
        producer_snapshot_identity=delivered.evidence.producer_snapshot_identity,
        verification_evidence=delivered.evidence,
    )
