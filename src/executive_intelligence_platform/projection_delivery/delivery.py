"""Website-facing projection delivery contract model.

The delivery boundary consumes only an existing ExecutiveIntelligenceProjection
and emits safe Website-facing metadata, indicators, and lineage references.
It does not validate snapshots, admit catalog entries, derive artifacts,
assemble packages, create projections, or implement Website behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from executive_intelligence_platform.executive_intelligence_package import (
    EXECUTIVE_INTELLIGENCE_PACKAGE_ASSEMBLY_RULE_VERSION,
    EXECUTIVE_INTELLIGENCE_PACKAGE_CONTRACT_VERSION,
    ExecutiveIntelligencePackageLineage,
)
from executive_intelligence_platform.executive_intelligence_projection import (
    EXECUTIVE_INTELLIGENCE_PROJECTION_CONTRACT_VERSION,
    EXECUTIVE_INTELLIGENCE_PROJECTION_RULE_VERSION,
    ExecutiveIntelligenceProjection,
    ExecutiveIntelligenceProjectionLineage,
)


WEBSITE_PROJECTION_DELIVERY_CONTRACT_VERSION = (
    "website-projection-delivery-contract-v1"
)
WEBSITE_PROJECTION_DELIVERY_PUBLICATION_POLICY_VERSION = (
    "website-projection-delivery-publication-policy-v1"
)

PASSING_PUBLICATION_STATE = "published"
PASSING_COMPATIBILITY_STATE = "compatible"
PASSING_AUTHORIZATION_SCOPE_STATE = "authorized"
PASSING_LINEAGE_STATE = "complete"
PASSING_LIMITATION_VISIBILITY_STATE = "visible"
PASSING_FRESHNESS_STATE = "current"
PASSING_CLASSIFICATION_STATE = "approved"
PASSING_CONTENT_SOURCE_TYPE = "governed_projection"

ALLOWED_PUBLICATION_STATES = (
    "draft",
    "pending_review",
    "published",
    "restricted",
    "revoked",
    "superseded",
    "expired",
    "unpublished",
)
ALLOWED_COMPATIBILITY_STATES = (
    "compatible",
    "incompatible",
    "unsupported_version",
    "lineage_incomplete",
    "restricted",
    "stale",
    "superseded",
    "unpublished",
    "unknown",
)
ALLOWED_FRESHNESS_STATES = (
    "current",
    "stale",
    "superseded",
    "expired",
    "unknown",
)
ALLOWED_CLASSIFICATIONS = (
    "public",
    "portal_operational",
    "client_confidential",
    "restricted_assessment",
)
DEFAULT_FIELD_CLASSIFICATIONS = (
    ("deliveryMetadata", "portal_operational"),
    ("projectionReference", "portal_operational"),
    ("publication", "portal_operational"),
    ("eligibility", "portal_operational"),
    ("compatibility", "portal_operational"),
    ("versionContext", "portal_operational"),
    ("lineage", "portal_operational"),
    ("classification", "portal_operational"),
    ("limitations", "portal_operational"),
)
DEFAULT_LIMITATIONS = (
    "delivery-contract-exposes-projection-metadata-and-lineage-only",
    "delivery-contract-does-not-include-raw-assessment-truth",
    "production-authority-is-preserved-from-projection-lineage",
    "website-must-not-recompute-assessment-truth",
)
WEBSITE_PROJECTION_DELIVERY_FAILURE_REASON_CODES = MappingProxyType(
    {
        "delivery-contract-version-missing": (
            "Delivery contract version is absent."
        ),
        "delivery-contract-version-unsupported": (
            "Delivery contract version is not supported."
        ),
        "projection-reference-missing": (
            "Projection identity or projection reference is absent."
        ),
        "projection-contract-version-unsupported": (
            "Projection contract version is unsupported."
        ),
        "projection-ineligible": (
            "Projection is not eligible for Website dashboard rendering."
        ),
        "publication-state-not-published": (
            "Publication state is not published."
        ),
        "compatibility-state-not-compatible": (
            "Compatibility state is not compatible."
        ),
        "authorization-scope-not-authorized": (
            "Authorization scope is not marked authorized for delivery."
        ),
        "lineage-state-incomplete": (
            "Required lineage is missing, incomplete, or ambiguous."
        ),
        "limitations-not-visible": (
            "Required limitation indicators are missing or not visible."
        ),
        "freshness-state-not-current": (
            "Projection freshness is stale, superseded, expired, or unknown."
        ),
        "classification-not-approved": (
            "Field or response classification is missing or not approved."
        ),
        "content-source-type-invalid": (
            "Content source type is missing, unknown, or mixed."
        ),
        "prohibited-field-present": (
            "Delivery representation contains a prohibited field."
        ),
        "delivery-payload-malformed": (
            "Delivery representation is structurally malformed."
        ),
        "upstream-projection-unavailable": (
            "The source projection is unavailable for delivery."
        ),
        "publication-policy-violation": (
            "Publication governance policy denied delivery."
        ),
    }
)

PROHIBITED_DELIVERY_KEYS = (
    "businessDecisionPackage",
    "sourcePackage",
    "sourceDerivedArtifact",
    "snapshotEvidence",
    "catalogEntry",
    "derivedArtifact",
    "decisionEvaluation",
    "businessReadinessSnapshot",
    "confidenceEvaluation",
    "recommendationPriorityEvaluation",
    "executiveSummaryFoundation",
    "rawEvidence",
    "sourceDocuments",
    "credentials",
    "secrets",
    "tokens",
    "stackTrace",
    "dashboardState",
)


@dataclass(frozen=True)
class WebsiteProjectionDeliveryIssue:
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
class WebsiteProjectionDeliveryRequest:
    delivery_contract_version: str = WEBSITE_PROJECTION_DELIVERY_CONTRACT_VERSION
    publication_policy_version: str = (
        WEBSITE_PROJECTION_DELIVERY_PUBLICATION_POLICY_VERSION
    )
    projection_eligible_for_dashboard: bool = True
    publication_state: str = PASSING_PUBLICATION_STATE
    compatibility_state: str = PASSING_COMPATIBILITY_STATE
    authorization_scope_state: str = PASSING_AUTHORIZATION_SCOPE_STATE
    lineage_state: str = PASSING_LINEAGE_STATE
    limitation_visibility_state: str = PASSING_LIMITATION_VISIBILITY_STATE
    freshness_state: str = PASSING_FRESHNESS_STATE
    classification_state: str = PASSING_CLASSIFICATION_STATE
    content_source_type: str = PASSING_CONTENT_SOURCE_TYPE
    limitations: tuple[str, ...] = DEFAULT_LIMITATIONS
    field_classifications: tuple[tuple[str, str], ...] = (
        DEFAULT_FIELD_CLASSIFICATIONS
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "deliveryContractVersion": self.delivery_contract_version,
            "publicationPolicyVersion": self.publication_policy_version,
            "projectionEligibleForDashboard": (
                self.projection_eligible_for_dashboard
            ),
            "publicationState": self.publication_state,
            "compatibilityState": self.compatibility_state,
            "authorizationScopeState": self.authorization_scope_state,
            "lineageState": self.lineage_state,
            "limitationVisibilityState": self.limitation_visibility_state,
            "freshnessState": self.freshness_state,
            "classificationState": self.classification_state,
            "contentSourceType": self.content_source_type,
            "limitations": list(self.limitations),
            "fieldClassifications": [
                {"fieldGroup": field_group, "classification": classification}
                for field_group, classification in self.field_classifications
            ],
        }


@dataclass(frozen=True)
class WebsiteProjectionDeliveryMetadata:
    delivery_contract_version: str
    publication_policy_version: str
    delivery_status: str
    content_source_type: str

    def to_dict(self) -> dict[str, str]:
        return {
            "deliveryContractVersion": self.delivery_contract_version,
            "publicationPolicyVersion": self.publication_policy_version,
            "deliveryStatus": self.delivery_status,
            "contentSourceType": self.content_source_type,
        }


@dataclass(frozen=True)
class WebsiteProjectionPublication:
    publication_state: str
    projection_eligible_for_dashboard: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "publicationState": self.publication_state,
            "projectionEligibleForDashboard": (
                self.projection_eligible_for_dashboard
            ),
        }


@dataclass(frozen=True)
class WebsiteProjectionDeliveryEligibility:
    projection_eligible_for_dashboard: bool
    publication_state: str
    compatibility_state: str
    authorization_scope_state: str
    lineage_state: str
    limitation_visibility_state: str
    freshness_state: str
    classification_state: str
    content_source_type: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "projectionEligibleForDashboard": (
                self.projection_eligible_for_dashboard
            ),
            "publicationState": self.publication_state,
            "compatibilityState": self.compatibility_state,
            "authorizationScopeState": self.authorization_scope_state,
            "lineageState": self.lineage_state,
            "limitationVisibilityState": self.limitation_visibility_state,
            "freshnessState": self.freshness_state,
            "classificationState": self.classification_state,
            "contentSourceType": self.content_source_type,
        }


@dataclass(frozen=True)
class WebsiteProjectionDeliveryCompatibility:
    delivery_contract_compatibility: str
    projection_contract_compatibility: str
    package_contract_compatibility: str
    snapshot_lineage_compatibility: str
    methodology_compatibility: str
    component_version_compatibility: str
    publication_policy_compatibility: str
    website_rendering_eligibility_compatibility: str

    def to_dict(self) -> dict[str, str]:
        return {
            "deliveryContractCompatibility": (
                self.delivery_contract_compatibility
            ),
            "projectionContractCompatibility": (
                self.projection_contract_compatibility
            ),
            "packageContractCompatibility": self.package_contract_compatibility,
            "snapshotLineageCompatibility": self.snapshot_lineage_compatibility,
            "methodologyCompatibility": self.methodology_compatibility,
            "componentVersionCompatibility": self.component_version_compatibility,
            "publicationPolicyCompatibility": (
                self.publication_policy_compatibility
            ),
            "websiteRenderingEligibilityCompatibility": (
                self.website_rendering_eligibility_compatibility
            ),
        }


@dataclass(frozen=True)
class WebsiteProjectionDeliveryVersionContext:
    delivery_contract_version: str
    publication_policy_version: str
    projection_contract_version: str
    projection_rule_version: str
    package_contract_version: str
    package_assembly_rule_version: str
    snapshot_response_contract_version: str
    business_decision_package_contract_version: str
    assessment_version: str
    methodology_version: str
    derivation_rule_version: str
    derivation_runtime_version: str
    component_version_references: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "deliveryContractVersion": self.delivery_contract_version,
            "publicationPolicyVersion": self.publication_policy_version,
            "projectionContractVersion": self.projection_contract_version,
            "projectionRuleVersion": self.projection_rule_version,
            "packageContractVersion": self.package_contract_version,
            "packageAssemblyRuleVersion": self.package_assembly_rule_version,
            "snapshotResponseContractVersion": (
                self.snapshot_response_contract_version
            ),
            "businessDecisionPackageContractVersion": (
                self.business_decision_package_contract_version
            ),
            "assessmentVersion": self.assessment_version,
            "methodologyVersion": self.methodology_version,
            "derivationRuleVersion": self.derivation_rule_version,
            "derivationRuntimeVersion": self.derivation_runtime_version,
            "componentVersionReferences": list(self.component_version_references),
        }


@dataclass(frozen=True)
class WebsiteProjectionDeliveryLineage:
    delivery_contract_version: str
    publication_policy_version: str
    producer_snapshot_identity: str
    projection_contract_version: str
    projection_rule_version: str
    package_contract_version: str
    package_assembly_rule_version: str
    derivation_rule_version: str
    derivation_runtime_version: str
    catalog_admission_policy_version: str
    catalog_admission_sequence: int
    snapshot_response_contract_version: str
    business_decision_package_contract_version: str
    assessment_version: str
    methodology_version: str
    production_authority: str
    source_component_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "delivery": {
                "deliveryContractVersion": self.delivery_contract_version,
                "publicationPolicyVersion": self.publication_policy_version,
            },
            "projection": {
                "producerSnapshotIdentity": self.producer_snapshot_identity,
                "projectionContractVersion": self.projection_contract_version,
                "projectionRuleVersion": self.projection_rule_version,
            },
            "package": {
                "producerSnapshotIdentity": self.producer_snapshot_identity,
                "packageContractVersion": self.package_contract_version,
                "packageAssemblyRuleVersion": (
                    self.package_assembly_rule_version
                ),
            },
            "derivation": {
                "producerSnapshotIdentity": self.producer_snapshot_identity,
                "derivationRuleVersion": self.derivation_rule_version,
                "derivationRuntimeVersion": self.derivation_runtime_version,
            },
            "catalog": {
                "producerSnapshotIdentity": self.producer_snapshot_identity,
                "admissionPolicyVersion": self.catalog_admission_policy_version,
                "admissionSequence": self.catalog_admission_sequence,
                "sourceComponentIds": list(self.source_component_ids),
            },
            "snapshot": {
                "producerSnapshotIdentity": self.producer_snapshot_identity,
                "snapshotResponseContractVersion": (
                    self.snapshot_response_contract_version
                ),
                "businessDecisionPackageContractVersion": (
                    self.business_decision_package_contract_version
                ),
                "assessmentVersion": self.assessment_version,
                "methodologyVersion": self.methodology_version,
                "productionAuthority": self.production_authority,
            },
            "assessmentServiceProvenance": {
                "producerSnapshotIdentity": self.producer_snapshot_identity,
                "sourceComponentIds": list(self.source_component_ids),
                "productionAuthority": self.production_authority,
            },
        }


@dataclass(frozen=True)
class WebsiteProjectionDeliveryClassification:
    classification_state: str
    response_classification: str
    field_classifications: tuple[tuple[str, str], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "classificationState": self.classification_state,
            "responseClassification": self.response_classification,
            "fieldClassifications": [
                {
                    "fieldGroup": field_group,
                    "classification": classification,
                }
                for field_group, classification in self.field_classifications
            ],
        }


@dataclass(frozen=True)
class WebsiteProjectionLimitations:
    limitation_visibility_state: str
    limitation_indicators: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "limitationVisibilityState": self.limitation_visibility_state,
            "limitationIndicators": list(self.limitation_indicators),
        }


@dataclass(frozen=True)
class WebsiteProjectionDelivery:
    delivery_metadata: WebsiteProjectionDeliveryMetadata
    projection_reference: WebsiteProjectionDeliveryLineage
    publication: WebsiteProjectionPublication
    eligibility: WebsiteProjectionDeliveryEligibility
    compatibility: WebsiteProjectionDeliveryCompatibility
    version_context: WebsiteProjectionDeliveryVersionContext
    lineage: WebsiteProjectionDeliveryLineage
    classification: WebsiteProjectionDeliveryClassification
    limitations: WebsiteProjectionLimitations

    def to_dict(self) -> dict[str, Any]:
        return {
            "deliveryMetadata": self.delivery_metadata.to_dict(),
            "projectionReference": {
                "producerSnapshotIdentity": (
                    self.projection_reference.producer_snapshot_identity
                ),
                "projectionContractVersion": (
                    self.projection_reference.projection_contract_version
                ),
                "projectionRuleVersion": (
                    self.projection_reference.projection_rule_version
                ),
            },
            "publication": self.publication.to_dict(),
            "eligibility": self.eligibility.to_dict(),
            "compatibility": self.compatibility.to_dict(),
            "versionContext": self.version_context.to_dict(),
            "lineage": self.lineage.to_dict(),
            "classification": self.classification.to_dict(),
            "limitations": self.limitations.to_dict(),
        }


@dataclass(frozen=True)
class WebsiteProjectionDeliveryResult:
    delivered: bool
    delivery: WebsiteProjectionDelivery | None
    issues: tuple[WebsiteProjectionDeliveryIssue, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "delivered": self.delivered,
            "delivery": (
                self.delivery.to_dict() if self.delivery is not None else None
            ),
            "issues": [issue.to_dict() for issue in self.issues],
        }


class WebsiteProjectionDeliveryPublisher:
    """Deterministic publisher for Website-facing projection delivery."""

    def publish(
        self,
        request: object,
        projection: object,
    ) -> WebsiteProjectionDeliveryResult:
        issues: list[WebsiteProjectionDeliveryIssue] = []

        issues.extend(_validate_request(request))

        if not isinstance(projection, ExecutiveIntelligenceProjection):
            issues.append(
                _issue(
                    "upstream-projection-unavailable",
                    "$.projection",
                    "Website delivery requires an ExecutiveIntelligenceProjection.",
                )
            )
            return _result(False, None, issues)

        issues.extend(_validate_projection(projection))
        if issues:
            return _result(False, None, issues)

        if not isinstance(request, WebsiteProjectionDeliveryRequest):
            return _result(False, None, issues)

        delivery = _build_delivery(request, projection)
        prohibited_path = _find_prohibited_key(delivery.to_dict())
        if prohibited_path is not None:
            return _result(
                False,
                None,
                [
                    _issue(
                        "prohibited-field-present",
                        prohibited_path,
                        "Delivery representation contains a prohibited field.",
                    )
                ],
            )

        return _result(True, delivery, [])


def _validate_request(
    request: object,
) -> list[WebsiteProjectionDeliveryIssue]:
    if not isinstance(request, WebsiteProjectionDeliveryRequest):
        return [
            _issue(
                "delivery-payload-malformed",
                "$.request",
                "Delivery request must be a WebsiteProjectionDeliveryRequest.",
            )
        ]

    issues: list[WebsiteProjectionDeliveryIssue] = []
    if not isinstance(request.delivery_contract_version, str) or not (
        request.delivery_contract_version.strip()
    ):
        issues.append(
            _issue(
                "delivery-contract-version-missing",
                "$.request.deliveryContractVersion",
                "Delivery contract version is required.",
            )
        )
    elif (
        request.delivery_contract_version
        != WEBSITE_PROJECTION_DELIVERY_CONTRACT_VERSION
    ):
        issues.append(
            _issue(
                "delivery-contract-version-unsupported",
                "$.request.deliveryContractVersion",
                "Delivery contract version is not supported.",
            )
        )

    if not isinstance(request.publication_policy_version, str) or not (
        request.publication_policy_version.strip()
    ):
        issues.append(
            _issue(
                "publication-policy-violation",
                "$.request.publicationPolicyVersion",
                "Publication policy version is required.",
            )
        )
    if request.publication_state != PASSING_PUBLICATION_STATE:
        issues.append(
            _issue(
                "publication-state-not-published",
                "$.request.publicationState",
                "Publication state must be published for Website delivery.",
            )
        )
    if request.projection_eligible_for_dashboard is not True:
        issues.append(
            _issue(
                "projection-ineligible",
                "$.request.projectionEligibleForDashboard",
                "Projection must be eligible for Website dashboard delivery.",
            )
        )
    if request.compatibility_state != PASSING_COMPATIBILITY_STATE:
        issues.append(
            _issue(
                "compatibility-state-not-compatible",
                "$.request.compatibilityState",
                "Compatibility state must be compatible.",
            )
        )
    if request.authorization_scope_state != PASSING_AUTHORIZATION_SCOPE_STATE:
        issues.append(
            _issue(
                "authorization-scope-not-authorized",
                "$.request.authorizationScopeState",
                "Authorization scope state must be authorized.",
            )
        )
    if request.lineage_state != PASSING_LINEAGE_STATE:
        issues.append(
            _issue(
                "lineage-state-incomplete",
                "$.request.lineageState",
                "Lineage state must be complete.",
            )
        )
    if request.limitation_visibility_state != PASSING_LIMITATION_VISIBILITY_STATE:
        issues.append(
            _issue(
                "limitations-not-visible",
                "$.request.limitationVisibilityState",
                "Limitation visibility state must be visible.",
            )
        )
    if request.freshness_state != PASSING_FRESHNESS_STATE:
        issues.append(
            _issue(
                "freshness-state-not-current",
                "$.request.freshnessState",
                "Freshness state must be current.",
            )
        )
    if request.classification_state != PASSING_CLASSIFICATION_STATE:
        issues.append(
            _issue(
                "classification-not-approved",
                "$.request.classificationState",
                "Classification state must be approved.",
            )
        )
    if request.content_source_type != PASSING_CONTENT_SOURCE_TYPE:
        issues.append(
            _issue(
                "content-source-type-invalid",
                "$.request.contentSourceType",
                "Content source type must be governed_projection.",
            )
        )
    if not _valid_string_tuple(request.limitations):
        issues.append(
            _issue(
                "limitations-not-visible",
                "$.request.limitations",
                "At least one limitation indicator is required.",
            )
        )
    if not _valid_field_classifications(request.field_classifications):
        issues.append(
            _issue(
                "classification-not-approved",
                "$.request.fieldClassifications",
                "Field classifications must be approved Website classifications.",
            )
        )

    return issues


def _validate_projection(
    projection: ExecutiveIntelligenceProjection,
) -> list[WebsiteProjectionDeliveryIssue]:
    issues: list[WebsiteProjectionDeliveryIssue] = []

    required_strings = {
        "producer_snapshot_identity": projection.producer_snapshot_identity,
        "projection_contract_version": projection.projection_contract_version,
        "projection_rule_version": projection.projection_rule_version,
        "package_contract_version": projection.package_contract_version,
        "package_assembly_rule_version": projection.package_assembly_rule_version,
        "snapshot_contract_version": projection.snapshot_contract_version,
        "assessment_version": projection.assessment_version,
        "methodology_version": projection.methodology_version,
        "derivation_rule_version": projection.derivation_rule_version,
        "derivation_runtime_version": projection.derivation_runtime_version,
    }
    for field_name, value in required_strings.items():
        if not isinstance(value, str) or not value.strip():
            issues.append(
                _issue(
                    "lineage-state-incomplete",
                    f"$.projection.{field_name}",
                    "Projection lineage field is incomplete.",
                )
            )

    if not isinstance(projection.lineage, ExecutiveIntelligenceProjectionLineage):
        issues.append(
            _issue(
                "lineage-state-incomplete",
                "$.projection.lineage",
                "Projection lineage is required.",
            )
        )
        return issues
    if not isinstance(
        projection.lineage.package_lineage,
        ExecutiveIntelligencePackageLineage,
    ):
        issues.append(
            _issue(
                "lineage-state-incomplete",
                "$.projection.lineage.packageLineage",
                "Projection package lineage is required.",
            )
        )
        return issues

    if projection.projection_contract_version != (
        EXECUTIVE_INTELLIGENCE_PROJECTION_CONTRACT_VERSION
    ):
        issues.append(
            _issue(
                "projection-contract-version-unsupported",
                "$.projection.projectionContractVersion",
                "Projection contract version is not supported for delivery.",
            )
        )
    if projection.projection_rule_version != (
        EXECUTIVE_INTELLIGENCE_PROJECTION_RULE_VERSION
    ):
        issues.append(
            _issue(
                "compatibility-state-not-compatible",
                "$.projection.projectionRuleVersion",
                "Projection rule version is not compatible for delivery.",
            )
        )
    if projection.package_contract_version != (
        EXECUTIVE_INTELLIGENCE_PACKAGE_CONTRACT_VERSION
    ):
        issues.append(
            _issue(
                "compatibility-state-not-compatible",
                "$.projection.packageContractVersion",
                "Package contract version is not compatible for delivery.",
            )
        )
    if projection.package_assembly_rule_version != (
        EXECUTIVE_INTELLIGENCE_PACKAGE_ASSEMBLY_RULE_VERSION
    ):
        issues.append(
            _issue(
                "compatibility-state-not-compatible",
                "$.projection.packageAssemblyRuleVersion",
                "Package assembly rule is not compatible for delivery.",
            )
        )

    issues.extend(_validate_projection_lineage_consistency(projection))
    return issues


def _validate_projection_lineage_consistency(
    projection: ExecutiveIntelligenceProjection,
) -> list[WebsiteProjectionDeliveryIssue]:
    issues: list[WebsiteProjectionDeliveryIssue] = []
    lineage = projection.lineage
    package_lineage = lineage.package_lineage
    catalog_metadata = package_lineage.catalog_admission_metadata
    producer_provenance = package_lineage.producer_provenance

    checks = (
        (
            projection.producer_snapshot_identity,
            lineage.producer_snapshot_identity,
            "$.projection.lineage.producerSnapshotIdentity",
        ),
        (
            projection.snapshot_contract_version,
            lineage.snapshot_contract_version,
            "$.projection.lineage.snapshotContractVersion",
        ),
        (
            projection.assessment_version,
            lineage.assessment_version,
            "$.projection.lineage.assessmentVersion",
        ),
        (
            projection.methodology_version,
            lineage.methodology_version,
            "$.projection.lineage.methodologyVersion",
        ),
        (
            projection.derivation_rule_version,
            lineage.derivation_rule_version,
            "$.projection.lineage.derivationRuleVersion",
        ),
        (
            projection.derivation_runtime_version,
            lineage.derivation_runtime_version,
            "$.projection.lineage.derivationRuntimeVersion",
        ),
        (
            projection.producer_snapshot_identity,
            package_lineage.producer_snapshot_identity,
            "$.projection.lineage.packageLineage.producerSnapshotIdentity",
        ),
        (
            projection.producer_snapshot_identity,
            catalog_metadata.producer_snapshot_identity,
            "$.projection.lineage.packageLineage.catalogAdmissionMetadata.producerSnapshotIdentity",
        ),
        (
            projection.producer_snapshot_identity,
            producer_provenance.producer_snapshot_identity,
            "$.projection.lineage.packageLineage.producerProvenance.producerSnapshotIdentity",
        ),
    )
    for left, right, path in checks:
        if left != right:
            issues.append(
                _issue(
                    "lineage-state-incomplete",
                    path,
                    "Projection lineage is inconsistent.",
                )
            )

    if not _valid_string_tuple(catalog_metadata.source_component_ids):
        issues.append(
            _issue(
                "lineage-state-incomplete",
                "$.projection.lineage.packageLineage.catalogAdmissionMetadata.sourceComponentIds",
                "Catalog source component lineage is incomplete.",
            )
        )
    if tuple(catalog_metadata.source_component_ids) != tuple(
        producer_provenance.source_component_ids
    ):
        issues.append(
            _issue(
                "lineage-state-incomplete",
                "$.projection.lineage.packageLineage.producerProvenance.sourceComponentIds",
                "Producer provenance source components are inconsistent.",
            )
        )
    if catalog_metadata.production_authority != (
        producer_provenance.production_authority
    ):
        issues.append(
            _issue(
                "lineage-state-incomplete",
                "$.projection.lineage.packageLineage.producerProvenance.productionAuthority",
                "Producer provenance production authority is inconsistent.",
            )
        )

    return issues


def _build_delivery(
    request: WebsiteProjectionDeliveryRequest,
    projection: ExecutiveIntelligenceProjection,
) -> WebsiteProjectionDelivery:
    package_lineage = projection.lineage.package_lineage
    catalog_metadata = package_lineage.catalog_admission_metadata
    producer_provenance = package_lineage.producer_provenance
    lineage = WebsiteProjectionDeliveryLineage(
        delivery_contract_version=request.delivery_contract_version,
        publication_policy_version=request.publication_policy_version,
        producer_snapshot_identity=projection.producer_snapshot_identity,
        projection_contract_version=projection.projection_contract_version,
        projection_rule_version=projection.projection_rule_version,
        package_contract_version=projection.package_contract_version,
        package_assembly_rule_version=projection.package_assembly_rule_version,
        derivation_rule_version=projection.derivation_rule_version,
        derivation_runtime_version=projection.derivation_runtime_version,
        catalog_admission_policy_version=catalog_metadata.admission_policy_version,
        catalog_admission_sequence=catalog_metadata.admission_sequence,
        snapshot_response_contract_version=projection.snapshot_contract_version,
        business_decision_package_contract_version=(
            catalog_metadata.package_contract_version
        ),
        assessment_version=projection.assessment_version,
        methodology_version=projection.methodology_version,
        production_authority=producer_provenance.production_authority,
        source_component_ids=tuple(producer_provenance.source_component_ids),
    )

    return WebsiteProjectionDelivery(
        delivery_metadata=WebsiteProjectionDeliveryMetadata(
            delivery_contract_version=request.delivery_contract_version,
            publication_policy_version=request.publication_policy_version,
            delivery_status="delivered",
            content_source_type=request.content_source_type,
        ),
        projection_reference=lineage,
        publication=WebsiteProjectionPublication(
            publication_state=request.publication_state,
            projection_eligible_for_dashboard=(
                request.projection_eligible_for_dashboard
            ),
        ),
        eligibility=WebsiteProjectionDeliveryEligibility(
            projection_eligible_for_dashboard=(
                request.projection_eligible_for_dashboard
            ),
            publication_state=request.publication_state,
            compatibility_state=request.compatibility_state,
            authorization_scope_state=request.authorization_scope_state,
            lineage_state=request.lineage_state,
            limitation_visibility_state=request.limitation_visibility_state,
            freshness_state=request.freshness_state,
            classification_state=request.classification_state,
            content_source_type=request.content_source_type,
        ),
        compatibility=WebsiteProjectionDeliveryCompatibility(
            delivery_contract_compatibility=request.compatibility_state,
            projection_contract_compatibility=request.compatibility_state,
            package_contract_compatibility=request.compatibility_state,
            snapshot_lineage_compatibility=request.compatibility_state,
            methodology_compatibility=request.compatibility_state,
            component_version_compatibility=request.compatibility_state,
            publication_policy_compatibility=request.compatibility_state,
            website_rendering_eligibility_compatibility=(
                request.compatibility_state
            ),
        ),
        version_context=WebsiteProjectionDeliveryVersionContext(
            delivery_contract_version=request.delivery_contract_version,
            publication_policy_version=request.publication_policy_version,
            projection_contract_version=projection.projection_contract_version,
            projection_rule_version=projection.projection_rule_version,
            package_contract_version=projection.package_contract_version,
            package_assembly_rule_version=projection.package_assembly_rule_version,
            snapshot_response_contract_version=projection.snapshot_contract_version,
            business_decision_package_contract_version=(
                catalog_metadata.package_contract_version
            ),
            assessment_version=projection.assessment_version,
            methodology_version=projection.methodology_version,
            derivation_rule_version=projection.derivation_rule_version,
            derivation_runtime_version=projection.derivation_runtime_version,
            component_version_references=tuple(
                catalog_metadata.source_component_ids
            ),
        ),
        lineage=lineage,
        classification=WebsiteProjectionDeliveryClassification(
            classification_state=request.classification_state,
            response_classification="portal_operational",
            field_classifications=tuple(request.field_classifications),
        ),
        limitations=WebsiteProjectionLimitations(
            limitation_visibility_state=request.limitation_visibility_state,
            limitation_indicators=tuple(request.limitations),
        ),
    )


def _valid_string_tuple(value: object) -> bool:
    return isinstance(value, tuple) and bool(value) and all(
        isinstance(item, str) and bool(item.strip()) for item in value
    )


def _valid_field_classifications(value: object) -> bool:
    if not isinstance(value, tuple) or not value:
        return False
    for item in value:
        if not isinstance(item, tuple) or len(item) != 2:
            return False
        field_group, classification = item
        if not isinstance(field_group, str) or not field_group.strip():
            return False
        if classification not in ALLOWED_CLASSIFICATIONS:
            return False
    return True


def _find_prohibited_key(value: object, path: str = "$") -> str | None:
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key in PROHIBITED_DELIVERY_KEYS:
                return child_path
            found = _find_prohibited_key(child, child_path)
            if found is not None:
                return found
    if isinstance(value, list):
        for index, child in enumerate(value):
            found = _find_prohibited_key(child, f"{path}[{index}]")
            if found is not None:
                return found
    return None


def _issue(
    code: str,
    path: str,
    message: str,
) -> WebsiteProjectionDeliveryIssue:
    if code not in WEBSITE_PROJECTION_DELIVERY_FAILURE_REASON_CODES:
        raise ValueError(f"Undocumented Website projection delivery issue: {code}.")
    return WebsiteProjectionDeliveryIssue(code=code, path=path, message=message)


def _result(
    delivered: bool,
    delivery: WebsiteProjectionDelivery | None,
    issues: list[WebsiteProjectionDeliveryIssue],
) -> WebsiteProjectionDeliveryResult:
    return WebsiteProjectionDeliveryResult(
        delivered=delivered,
        delivery=delivery,
        issues=tuple(issues),
    )
