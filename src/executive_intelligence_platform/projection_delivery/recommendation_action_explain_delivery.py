"""Non-releasable, versioned local v3 recommendation-action delivery candidate.

The content projection is a strict schema for future authorized delivery. This
module supplies no publication, principal authorization, or client response.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from executive_intelligence_platform.projection_delivery.verified_admission import (
    LOCAL_V3_PACKAGE_VERSION,
    VerifiedAdmissionError,
)
from executive_intelligence_platform.snapshot_compatibility.compatibility import (
    SUPPORTED_METHODOLOGY_VERSION,
)
from executive_intelligence_platform.snapshot_derivation.local_v3_recommendation_projection import (
    LocalV3Recommendation,
    LocalV3RecommendationProjection,
    project_local_v3_recommendations,
)


RECOMMENDATION_ACTION_EXPLAIN_DELIVERY_CONTRACT_VERSION = (
    "website-recommendation-action-explain-delivery-contract-v1"
)


@dataclass(frozen=True, slots=True)
class RecommendationActionContentItem:
    recommendation_action_text: str


@dataclass(frozen=True, slots=True)
class RecommendationActionContentProjection:
    """Only the approved recommendation value; no trusted metadata."""

    recommendations: tuple[RecommendationActionContentItem, ...]

    def to_dict(self) -> dict[str, object]:
        """Build only the exact approved content shape, as a fresh copy."""
        return {
            "recommendations": [
                {"recommendationActionText": item.recommendation_action_text}
                for item in self.recommendations
            ]
        }


@dataclass(frozen=True, slots=True)
class InternalRecommendationActionExplainDeliveryCandidate:
    """Trusted local candidate; deliberately has no release serializer."""

    delivery_contract_version: str
    verified_projection: LocalV3RecommendationProjection
    content: RecommendationActionContentProjection
    release_eligible: bool = field(default=False, init=False)


def prepare_recommendation_action_explain_delivery(
    gateway: object,
    admission: object,
    *,
    package_contract_version: str,
    delivery_contract_version: str,
) -> InternalRecommendationActionExplainDeliveryCandidate:
    """Reverify signed v3 truth and prepare one non-releasable local candidate."""
    if (type(delivery_contract_version) is not str or
            delivery_contract_version !=
            RECOMMENDATION_ACTION_EXPLAIN_DELIVERY_CONTRACT_VERSION):
        raise VerifiedAdmissionError("unsupported-recommendation-action-delivery-version")
    if (type(package_contract_version) is not str or
            package_contract_version != LOCAL_V3_PACKAGE_VERSION):
        raise VerifiedAdmissionError("unsupported-local-package-version")

    projection = project_local_v3_recommendations(
        gateway, admission, package_contract_version=package_contract_version,
    )
    if (type(projection) is not LocalV3RecommendationProjection or
            projection.release_eligible is not False or
            projection.package_contract_version != LOCAL_V3_PACKAGE_VERSION or
            projection.methodology_version != SUPPORTED_METHODOLOGY_VERSION or
            type(projection.recommendations) is not tuple or
            not projection.recommendations or
            any(type(item) is not LocalV3Recommendation for item in
                projection.recommendations)):
        raise VerifiedAdmissionError("invalid-recommendation-action-projection")

    content = RecommendationActionContentProjection(tuple(
        RecommendationActionContentItem(item.recommendation_action_text)
        for item in projection.recommendations
    ))
    # Validate the entire schema at this boundary, before retaining a candidate.
    payload = content.to_dict()
    if (type(payload) is not dict or tuple(payload) != ("recommendations",) or
            type(payload["recommendations"]) is not list or
            len(payload["recommendations"]) != len(projection.recommendations) or
            any(type(row) is not dict or tuple(row) !=
                ("recommendationActionText",) or
                type(row["recommendationActionText"]) is not str or
                row["recommendationActionText"] != source.recommendation_action_text
                for row, source in zip(payload["recommendations"],
                                       projection.recommendations))):
        raise VerifiedAdmissionError("invalid-recommendation-action-content")

    return InternalRecommendationActionExplainDeliveryCandidate(
        delivery_contract_version=delivery_contract_version,
        verified_projection=projection,
        content=content,
    )
