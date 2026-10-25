import json
import sys
import unittest
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from executive_intelligence_platform.executive_intelligence_package import (  # noqa: E402
    EXECUTIVE_INTELLIGENCE_PACKAGE_ASSEMBLY_RULE_VERSION,
    EXECUTIVE_INTELLIGENCE_PACKAGE_CONTRACT_VERSION,
    ExecutiveIntelligencePackageAssembler,
    ExecutiveIntelligencePackageRequest,
)
from executive_intelligence_platform.executive_intelligence_projection import (  # noqa: E402
    EXECUTIVE_INTELLIGENCE_PROJECTION_CONTRACT_VERSION,
    EXECUTIVE_INTELLIGENCE_PROJECTION_RULE_VERSION,
    ExecutiveIntelligenceProjection,
    ExecutiveIntelligenceProjectionLineage,
    ExecutiveIntelligenceProjectionProjector,
    ExecutiveIntelligenceProjectionRequest,
)
from executive_intelligence_platform.projection_delivery import (  # noqa: E402
    WEBSITE_PROJECTION_DELIVERY_CONTRACT_VERSION,
    WEBSITE_PROJECTION_DELIVERY_FAILURE_REASON_CODES,
    WEBSITE_PROJECTION_DELIVERY_PUBLICATION_POLICY_VERSION,
    WebsiteProjectionDeliveryContractPublisher,
    WebsiteProjectionDeliveryPublisher,
    WebsiteProjectionDeliveryRequest,
    WebsiteProjectionContentItem,
    WebsiteProjectionContentSection,
    WebsiteProjectionDashboardContent,
    WebsiteProjectionDisplayField,
    WebsiteProjectionRenderingGuidance,
)
from executive_intelligence_platform.projection_delivery.delivery import (  # noqa: E402
    _MAX_SERIALIZED_JSON_CANDIDATE_CHARS,
    _MAX_SERIALIZED_JSON_CONTAINER_DEPTH,
    _find_prohibited_key,
)
from executive_intelligence_platform.snapshot_catalog import (  # noqa: E402
    SnapshotCatalog,
)
from executive_intelligence_platform.snapshot_derivation import (  # noqa: E402
    SNAPSHOT_DERIVATION_RULE_VERSION,
    SNAPSHOT_DERIVATION_RUNTIME_VERSION,
    SnapshotDerivationRequest,
    SnapshotDerivationRuntime,
)


PRODUCER_SNAPSHOT_IDENTITY = "assessment-service-snapshot-001"
APPROVED_FIELD_CLASSIFICATIONS = (
    ("deliveryMetadata", "portal_operational"),
    ("projectionReference", "portal_operational"),
    ("publication", "portal_operational"),
    ("eligibility", "portal_operational"),
    ("compatibility", "portal_operational"),
    ("versionContext", "portal_operational"),
    ("lineage", "portal_operational"),
    ("classification", "portal_operational"),
    ("limitations", "portal_operational"),
    ("dashboardContent", "restricted_assessment"),
    ("renderingGuidance", "portal_operational"),
)


def valid_snapshot():
    return {
        "responseContractVersion": "executive-runtime-response-v1",
        "responseStatus": {
            "packageValidation": "VALIDATED",
            "runtimeEligibility": "RUNTIME_ELIGIBLE",
            "exposure": "EXPOSURE_ELIGIBLE",
            "productionAuthority": "NOT_PRODUCTION_AUTHORITATIVE",
        },
        "businessDecisionPackage": {
            "decisionEvaluation": {
                "overallScore": 78.0,
                "totalWeight": 10.0,
                "questionCount": 5,
            },
            "businessReadinessSnapshot": {
                "overallReadiness": {
                    "score": 78.0,
                },
                "audit": {
                    "questionCount": 5,
                    "totalWeight": 10.0,
                },
            },
            "confidenceEvaluation": {},
            "recommendationPriorityEvaluation": {},
            "executiveSummaryFoundation": {},
            "audit": {
                "assessmentVersion": "nguyen-ai-executive-assessment-v1",
                "methodologyVersion": "business-decision-methodology-v1",
                "sourceComponentIds": [
                    "decisionEvaluation",
                    "businessReadinessSnapshot",
                    "confidenceEvaluation",
                    "recommendationPriorityEvaluation",
                    "executiveSummaryFoundation",
                ],
                "evaluatedDimensions": ["ai-readiness"],
                "questionCount": 5,
                "totalWeight": 10.0,
            },
            "limitations": [
                "final-confidence-formulas-not-implemented",
                "final-confidence-level-assignment-not-implemented",
                "final-recommendation-assignment-not-implemented",
                "recommendation-generation-not-implemented",
                "service-decisions-not-implemented",
                "executive-reporting-not-implemented",
                "executive-narratives-not-implemented",
                "evidence-ingestion-not-implemented",
                "persistence-not-implemented",
                "api-exposure-of-snapshot-consumers-not-implemented",
            ],
            "versionMetadata": {
                "contractVersion": "business-decision-package-v1",
                "assessmentVersion": "nguyen-ai-executive-assessment-v1",
                "methodologyVersion": "business-decision-methodology-v1",
                "componentVersions": {
                    "decisionEvaluation": "assessment-decision-engine-v2",
                    "businessReadinessSnapshot": "sprint3-snapshot-foundation-v1",
                    "confidenceEvaluation": "sprint3-confidence-foundation-v1",
                    "recommendationPriorityEvaluation": (
                        "sprint3-recommendation-priority-foundation-v1"
                    ),
                    "executiveSummaryFoundation": (
                        "sprint3-executive-summary-foundation-v1"
                    ),
                },
            },
        },
    }


def executive_projection():
    catalog = SnapshotCatalog()
    admission_result = catalog.admit(
        valid_snapshot(),
        producer_snapshot_identity=PRODUCER_SNAPSHOT_IDENTITY,
    )
    derivation_result = SnapshotDerivationRuntime().derive(
        admission_result.entry,
        SnapshotDerivationRequest(),
    )
    package_result = ExecutiveIntelligencePackageAssembler().assemble(
        ExecutiveIntelligencePackageRequest(),
        derivation_result.artifact,
    )
    projection_result = ExecutiveIntelligenceProjectionProjector().project(
        ExecutiveIntelligenceProjectionRequest(),
        package_result.package,
    )
    return projection_result.projection


def delivery_result(request=None, projection=None):
    return WebsiteProjectionDeliveryPublisher().publish(
        WebsiteProjectionDeliveryRequest() if request is None else request,
        executive_projection() if projection is None else projection,
    )


def published_contract_instance(delivery=None):
    return WebsiteProjectionDeliveryContractPublisher().publish(
        delivery_result() if delivery is None else delivery
    )


def approved_dashboard_content():
    return WebsiteProjectionDashboardContent(
        sections=(
            (
                "summaries",
                WebsiteProjectionContentSection(
                    label="Executive Summary",
                    items=(
                        WebsiteProjectionContentItem(
                            label="Governed Status",
                            summary="Approved projection content supplied by EIP.",
                            semantic_intent="status_summary",
                            fields=(
                                WebsiteProjectionDisplayField(
                                    label="Status",
                                    value="Published",
                                ),
                            ),
                        ),
                    ),
                ),
            ),
            (
                "metrics",
                WebsiteProjectionContentSection(
                    label="Version Metrics",
                    items=(
                        WebsiteProjectionContentItem(
                            label="Contract Version",
                            value=1,
                            unit="version",
                            fields=(
                                WebsiteProjectionDisplayField(
                                    label="Delivery Contract",
                                    value=WEBSITE_PROJECTION_DELIVERY_CONTRACT_VERSION,
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        )
    )


def approved_rendering_guidance():
    return WebsiteProjectionRenderingGuidance(
        section_order=("summaries", "metrics"),
    )


def dashboard_text_request(value):
    content = WebsiteProjectionDashboardContent(
        sections=(
            (
                "summaries",
                WebsiteProjectionContentSection(
                    label="Executive Summary",
                    items=(
                        WebsiteProjectionContentItem(
                            label="Text",
                            fields=(
                                WebsiteProjectionDisplayField(label="Text", value=value),
                            ),
                        ),
                    ),
                ),
            ),
        )
    )
    return WebsiteProjectionDeliveryRequest(
        field_classifications=APPROVED_FIELD_CLASSIFICATIONS,
        dashboard_content=content,
    )


def delivery_result_with_content():
    return delivery_result(
        WebsiteProjectionDeliveryRequest(
            field_classifications=APPROVED_FIELD_CLASSIFICATIONS,
            dashboard_content=approved_dashboard_content(),
            rendering_guidance=approved_rendering_guidance(),
        )
    )


def issue_codes(result):
    return tuple(issue.code for issue in result.issues)


def contains_key(value, key_name):
    if isinstance(value, dict):
        return key_name in value or any(
            contains_key(child, key_name) for child in value.values()
        )
    if isinstance(value, list):
        return any(contains_key(child, key_name) for child in value)
    return False


class WebsiteProjectionDeliveryTests(unittest.TestCase):
    def test_generates_valid_delivery_from_existing_projection(self):
        result = delivery_result()

        self.assertTrue(result.delivered)
        self.assertEqual(result.issues, ())
        self.assertIsNotNone(result.delivery)
        self.assertEqual(
            result.delivery.delivery_metadata.delivery_status,
            "delivered",
        )

    def test_delivery_contract_version_is_explicit(self):
        result = delivery_result()

        self.assertEqual(
            result.delivery.delivery_metadata.delivery_contract_version,
            WEBSITE_PROJECTION_DELIVERY_CONTRACT_VERSION,
        )
        self.assertEqual(
            result.delivery.to_dict()["deliveryMetadata"][
                "deliveryContractVersion"
            ],
            WEBSITE_PROJECTION_DELIVERY_CONTRACT_VERSION,
        )

    def test_preserves_lineage_references(self):
        result = delivery_result()
        lineage = result.delivery.lineage

        self.assertEqual(lineage.producer_snapshot_identity, PRODUCER_SNAPSHOT_IDENTITY)
        self.assertEqual(
            lineage.catalog_admission_policy_version,
            "snapshot-catalog-admission-v1",
        )
        self.assertEqual(lineage.catalog_admission_sequence, 1)
        self.assertEqual(lineage.production_authority, "NOT_PRODUCTION_AUTHORITATIVE")
        self.assertEqual(
            lineage.source_component_ids,
            (
                "decisionEvaluation",
                "businessReadinessSnapshot",
                "confidenceEvaluation",
                "recommendationPriorityEvaluation",
                "executiveSummaryFoundation",
            ),
        )

    def test_preserves_version_context(self):
        result = delivery_result()
        versions = result.delivery.version_context

        self.assertEqual(
            versions.delivery_contract_version,
            WEBSITE_PROJECTION_DELIVERY_CONTRACT_VERSION,
        )
        self.assertEqual(
            versions.publication_policy_version,
            WEBSITE_PROJECTION_DELIVERY_PUBLICATION_POLICY_VERSION,
        )
        self.assertEqual(
            versions.projection_contract_version,
            EXECUTIVE_INTELLIGENCE_PROJECTION_CONTRACT_VERSION,
        )
        self.assertEqual(
            versions.projection_rule_version,
            EXECUTIVE_INTELLIGENCE_PROJECTION_RULE_VERSION,
        )
        self.assertEqual(
            versions.package_contract_version,
            EXECUTIVE_INTELLIGENCE_PACKAGE_CONTRACT_VERSION,
        )
        self.assertEqual(
            versions.package_assembly_rule_version,
            EXECUTIVE_INTELLIGENCE_PACKAGE_ASSEMBLY_RULE_VERSION,
        )
        self.assertEqual(
            versions.snapshot_response_contract_version,
            "executive-runtime-response-v1",
        )
        self.assertEqual(
            versions.business_decision_package_contract_version,
            "business-decision-package-v1",
        )
        self.assertEqual(
            versions.assessment_version,
            "nguyen-ai-executive-assessment-v1",
        )
        self.assertEqual(
            versions.methodology_version,
            "business-decision-methodology-v1",
        )
        self.assertEqual(
            versions.derivation_rule_version,
            SNAPSHOT_DERIVATION_RULE_VERSION,
        )
        self.assertEqual(
            versions.derivation_runtime_version,
            SNAPSHOT_DERIVATION_RUNTIME_VERSION,
        )

    def test_publication_gating_fails_closed(self):
        result = delivery_result(
            WebsiteProjectionDeliveryRequest(publication_state="draft")
        )

        self.assertFalse(result.delivered)
        self.assertIsNone(result.delivery)
        self.assertEqual(issue_codes(result), ("publication-state-not-published",))

    def test_eligibility_gating_fails_closed(self):
        result = delivery_result(
            WebsiteProjectionDeliveryRequest(projection_eligible_for_dashboard=False)
        )

        self.assertFalse(result.delivered)
        self.assertIsNone(result.delivery)
        self.assertEqual(issue_codes(result), ("projection-ineligible",))

    def test_compatibility_gating_fails_closed(self):
        result = delivery_result(
            WebsiteProjectionDeliveryRequest(compatibility_state="incompatible")
        )

        self.assertFalse(result.delivered)
        self.assertIsNone(result.delivery)
        self.assertEqual(issue_codes(result), ("compatibility-state-not-compatible",))

    def test_freshness_gating_fails_closed(self):
        result = delivery_result(
            WebsiteProjectionDeliveryRequest(freshness_state="stale")
        )

        self.assertFalse(result.delivered)
        self.assertIsNone(result.delivery)
        self.assertEqual(issue_codes(result), ("freshness-state-not-current",))

    def test_classification_gating_fails_closed(self):
        result = delivery_result(
            WebsiteProjectionDeliveryRequest(classification_state="restricted")
        )

        self.assertFalse(result.delivered)
        self.assertIsNone(result.delivery)
        self.assertEqual(issue_codes(result), ("classification-not-approved",))

    def test_limitation_gating_fails_closed(self):
        result = delivery_result(
            WebsiteProjectionDeliveryRequest(limitations=())
        )

        self.assertFalse(result.delivered)
        self.assertIsNone(result.delivery)
        self.assertEqual(issue_codes(result), ("limitations-not-visible",))

    def test_authorization_scope_gating_fails_closed(self):
        result = delivery_result(
            WebsiteProjectionDeliveryRequest(authorization_scope_state="unauthorized")
        )

        self.assertFalse(result.delivered)
        self.assertIsNone(result.delivery)
        self.assertEqual(issue_codes(result), ("authorization-scope-not-authorized",))

    def test_content_source_type_gating_fails_closed(self):
        result = delivery_result(
            WebsiteProjectionDeliveryRequest(
                content_source_type="synthetic_demonstration"
            )
        )

        self.assertFalse(result.delivered)
        self.assertIsNone(result.delivery)
        self.assertEqual(issue_codes(result), ("content-source-type-invalid",))

    def test_unsupported_delivery_contract_fails_closed(self):
        result = delivery_result(
            WebsiteProjectionDeliveryRequest(
                delivery_contract_version="website-projection-delivery-contract-v2"
            )
        )

        self.assertFalse(result.delivered)
        self.assertIsNone(result.delivery)
        self.assertEqual(
            issue_codes(result),
            ("delivery-contract-version-unsupported",),
        )

    def test_missing_delivery_contract_fails_closed(self):
        result = delivery_result(
            WebsiteProjectionDeliveryRequest(delivery_contract_version="")
        )

        self.assertFalse(result.delivered)
        self.assertIsNone(result.delivery)
        self.assertEqual(
            issue_codes(result),
            ("delivery-contract-version-missing",),
        )

    def test_output_is_deterministic(self):
        projection = executive_projection()
        request = WebsiteProjectionDeliveryRequest()
        publisher = WebsiteProjectionDeliveryPublisher()

        first_result = publisher.publish(request, projection)
        second_result = publisher.publish(request, projection)

        self.assertEqual(first_result, second_result)
        self.assertEqual(first_result.to_dict(), second_result.to_dict())

    def test_delivery_models_are_immutable(self):
        result = delivery_result()

        with self.assertRaises(FrozenInstanceError):
            result.delivered = False

        with self.assertRaises(FrozenInstanceError):
            result.delivery.lineage.producer_snapshot_identity = "changed"

        with self.assertRaises(FrozenInstanceError):
            result.delivery.eligibility.freshness_state = "stale"

    def test_prohibited_fields_are_excluded_from_delivery_output(self):
        delivery = delivery_result().delivery.to_dict()

        prohibited_keys = (
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
            "credentials",
            "secrets",
            "tokens",
            "stackTrace",
            "dashboardState",
        )
        for key in prohibited_keys:
            self.assertFalse(contains_key(delivery, key), key)

    def test_source_projection_is_not_mutated(self):
        projection = executive_projection()
        before = projection.to_dict()

        WebsiteProjectionDeliveryPublisher().publish(
            WebsiteProjectionDeliveryRequest(),
            projection,
        )

        self.assertEqual(projection.to_dict(), before)

    def test_invalid_input_fails_closed(self):
        result = WebsiteProjectionDeliveryPublisher().publish(
            WebsiteProjectionDeliveryRequest(),
            valid_snapshot(),
        )

        self.assertFalse(result.delivered)
        self.assertIsNone(result.delivery)
        self.assertEqual(issue_codes(result), ("upstream-projection-unavailable",))

    def test_stable_fail_closed_reason_codes_are_documented(self):
        expected_codes = {
            "delivery-contract-version-missing",
            "delivery-contract-version-unsupported",
            "projection-reference-missing",
            "projection-contract-version-unsupported",
            "projection-ineligible",
            "publication-state-not-published",
            "compatibility-state-not-compatible",
            "authorization-scope-not-authorized",
            "lineage-state-incomplete",
            "limitations-not-visible",
            "freshness-state-not-current",
            "classification-not-approved",
            "content-source-type-invalid",
            "prohibited-field-present",
            "delivery-payload-malformed",
            "upstream-projection-unavailable",
            "publication-policy-violation",
        }

        self.assertEqual(
            set(WEBSITE_PROJECTION_DELIVERY_FAILURE_REASON_CODES),
            expected_codes,
        )
        for code, description in (
            WEBSITE_PROJECTION_DELIVERY_FAILURE_REASON_CODES.items()
        ):
            self.assertIsInstance(code, str)
            self.assertRegex(code, r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
            self.assertIsInstance(description, str)
            self.assertTrue(description.strip())

    def test_incomplete_projection_lineage_fails_closed(self):
        source = executive_projection()
        projection = ExecutiveIntelligenceProjection(
            projection_contract_version=source.projection_contract_version,
            projection_rule_version=source.projection_rule_version,
            package_contract_version=source.package_contract_version,
            package_assembly_rule_version=source.package_assembly_rule_version,
            producer_snapshot_identity="",
            snapshot_contract_version=source.snapshot_contract_version,
            assessment_version=source.assessment_version,
            methodology_version=source.methodology_version,
            derivation_rule_version=source.derivation_rule_version,
            derivation_runtime_version=source.derivation_runtime_version,
            lineage=source.lineage,
            source_package=source.source_package,
        )

        result = delivery_result(projection=projection)

        self.assertFalse(result.delivered)
        self.assertIsNone(result.delivery)
        self.assertIn("lineage-state-incomplete", issue_codes(result))

    def test_unsupported_projection_contract_fails_closed(self):
        source = executive_projection()
        projection = ExecutiveIntelligenceProjection(
            projection_contract_version="executive-intelligence-projection-v2",
            projection_rule_version=source.projection_rule_version,
            package_contract_version=source.package_contract_version,
            package_assembly_rule_version=source.package_assembly_rule_version,
            producer_snapshot_identity=source.producer_snapshot_identity,
            snapshot_contract_version=source.snapshot_contract_version,
            assessment_version=source.assessment_version,
            methodology_version=source.methodology_version,
            derivation_rule_version=source.derivation_rule_version,
            derivation_runtime_version=source.derivation_runtime_version,
            lineage=source.lineage,
            source_package=source.source_package,
        )

        result = delivery_result(projection=projection)

        self.assertFalse(result.delivered)
        self.assertIsNone(result.delivery)
        self.assertIn("projection-contract-version-unsupported", issue_codes(result))

    def test_delivery_reuses_projection_without_snapshot_or_derivation_work(self):
        projection = executive_projection()
        publisher = WebsiteProjectionDeliveryPublisher()
        request = WebsiteProjectionDeliveryRequest()

        with patch(
            "executive_intelligence_platform.snapshot_compatibility.validate_snapshot_compatibility",
            side_effect=AssertionError("snapshot validation must not be called"),
        ), patch.object(
            SnapshotCatalog,
            "admit",
            side_effect=AssertionError("catalog admission must not be called"),
        ), patch.object(
            SnapshotDerivationRuntime,
            "derive",
            side_effect=AssertionError("derivation must not be called"),
        ):
            result = publisher.publish(request, projection)

        self.assertTrue(result.delivered)
        self.assertEqual(result.issues, ())

    def test_rejects_projection_with_invalid_embedded_package(self):
        source = executive_projection()
        invalid_package = replace(source.source_package, source_derived_artifact=None)
        forged = replace(source, source_package=invalid_package)

        result = delivery_result(projection=forged)

        self.assertFalse(result.delivered)
        self.assertIsNone(result.delivery)
        self.assertEqual(issue_codes(result), ("upstream-projection-unavailable",))
        self.assertIs(forged.source_package, invalid_package)
        self.assertIsNone(invalid_package.source_derived_artifact)

    def test_rejects_projection_with_conflicting_package_metadata(self):
        source = executive_projection()
        package = source.source_package
        invalid_package = replace(
            package,
            assessment_version="conflicting-assessment",
            lineage=replace(
                package.lineage, assessment_version="conflicting-assessment"
            ),
        )
        forged = replace(source, source_package=invalid_package)
        before = forged.to_dict()

        result = delivery_result(projection=forged)

        self.assertFalse(result.delivered)
        self.assertIsNone(result.delivery)
        self.assertEqual(issue_codes(result), ("upstream-projection-unavailable",))
        self.assertEqual(forged.to_dict(), before)

    def test_rejects_projection_conflicting_with_valid_source_package(self):
        source = executive_projection()
        forged = replace(
            source,
            assessment_version="conflicting-assessment",
            lineage=replace(
                source.lineage, assessment_version="conflicting-assessment"
            ),
        )
        before = forged.to_dict()

        result = delivery_result(projection=forged)

        self.assertFalse(result.delivered)
        self.assertIsNone(result.delivery)
        self.assertEqual(issue_codes(result), ("lineage-state-incomplete",))
        self.assertEqual(forged.to_dict(), before)

    def test_delivery_output_contains_no_assessment_service_business_logic(self):
        delivery = delivery_result().delivery.to_dict()

        business_truth_keys = (
            "overallScore",
            "totalWeight",
            "questionCount",
            "overallReadiness",
            "readiness",
            "confidence",
            "recommendation",
            "priority",
            "score",
            "weight",
        )
        for key in business_truth_keys:
            self.assertFalse(contains_key(delivery, key), key)

    def test_publishes_delivery_contract_instance_deterministically(self):
        source_delivery_result = delivery_result()

        first = WebsiteProjectionDeliveryContractPublisher().publish(
            source_delivery_result
        )
        second = WebsiteProjectionDeliveryContractPublisher().publish(
            source_delivery_result
        )

        self.assertTrue(first.published)
        self.assertEqual(first.issues, ())
        self.assertEqual(first, second)
        self.assertEqual(first.to_dict(), second.to_dict())

    def test_published_contract_instance_preserves_contract_identity(self):
        source_delivery_result = delivery_result()

        publication = published_contract_instance(source_delivery_result)

        self.assertEqual(
            publication.contract_instance.delivery_contract_version,
            WEBSITE_PROJECTION_DELIVERY_CONTRACT_VERSION,
        )
        self.assertEqual(
            publication.contract_instance.publication_policy_version,
            WEBSITE_PROJECTION_DELIVERY_PUBLICATION_POLICY_VERSION,
        )
        self.assertEqual(
            publication.contract_instance.to_dict(),
            source_delivery_result.delivery.to_dict(),
        )

    def test_published_contract_instance_preserves_lineage_versions_and_metadata(
        self,
    ):
        source_delivery_result = delivery_result()

        publication = published_contract_instance(source_delivery_result)
        contract_payload = publication.contract_instance.to_dict()
        delivery_payload = source_delivery_result.delivery.to_dict()

        self.assertEqual(
            contract_payload["lineage"],
            delivery_payload["lineage"],
        )
        self.assertEqual(
            contract_payload["versionContext"],
            delivery_payload["versionContext"],
        )
        self.assertEqual(
            contract_payload["deliveryMetadata"],
            delivery_payload["deliveryMetadata"],
        )
        self.assertEqual(
            contract_payload["publication"],
            delivery_payload["publication"],
        )

    def test_published_contract_instance_preserves_governance_indicators(self):
        source_delivery_result = delivery_result()

        publication = published_contract_instance(source_delivery_result)
        contract_payload = publication.contract_instance.to_dict()
        delivery_payload = source_delivery_result.delivery.to_dict()

        self.assertEqual(
            contract_payload["eligibility"],
            delivery_payload["eligibility"],
        )
        self.assertEqual(
            contract_payload["compatibility"],
            delivery_payload["compatibility"],
        )
        self.assertEqual(
            contract_payload["classification"],
            delivery_payload["classification"],
        )
        self.assertEqual(
            contract_payload["limitations"],
            delivery_payload["limitations"],
        )

    def test_published_contract_instance_is_immutable(self):
        publication = published_contract_instance()

        with self.assertRaises(FrozenInstanceError):
            publication.published = False

        with self.assertRaises(FrozenInstanceError):
            publication.contract_instance.delivery = None

        with self.assertRaises(FrozenInstanceError):
            publication.contract_instance.delivery.lineage.assessment_version = (
                "changed"
            )

    def test_contract_instance_serialization_is_deterministic(self):
        publication = published_contract_instance()

        first = publication.contract_instance.serialize()
        second = publication.contract_instance.serialize()

        self.assertEqual(first, second)
        self.assertEqual(json.loads(first), publication.contract_instance.to_dict())
        self.assertEqual(
            first,
            json.dumps(
                publication.contract_instance.to_dict(),
                ensure_ascii=True,
                separators=(",", ":"),
                sort_keys=True,
            ),
        )

    def test_contract_publication_preserves_delivery_result_immutability(self):
        source_delivery_result = delivery_result()
        before = source_delivery_result.to_dict()

        WebsiteProjectionDeliveryContractPublisher().publish(
            source_delivery_result
        )

        self.assertEqual(source_delivery_result.to_dict(), before)

    def test_contract_publication_excludes_prohibited_upstream_artifacts(self):
        publication = published_contract_instance()
        contract_payload = publication.contract_instance.to_dict()

        prohibited_keys = (
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
            "credentials",
            "secrets",
            "tokens",
            "stackTrace",
            "dashboardState",
        )
        for key in prohibited_keys:
            self.assertFalse(contains_key(contract_payload, key), key)

    def test_contract_publication_fails_closed_for_unsuccessful_delivery(self):
        unsuccessful_delivery = delivery_result(
            WebsiteProjectionDeliveryRequest(publication_state="draft")
        )

        publication = WebsiteProjectionDeliveryContractPublisher().publish(
            unsuccessful_delivery
        )

        self.assertFalse(publication.published)
        self.assertIsNone(publication.contract_instance)
        self.assertEqual(
            issue_codes(publication),
            ("publication-state-not-published",),
        )

    def test_contract_publication_fails_closed_for_invalid_input(self):
        publication = WebsiteProjectionDeliveryContractPublisher().publish(
            valid_snapshot()
        )

        self.assertFalse(publication.published)
        self.assertIsNone(publication.contract_instance)
        self.assertEqual(issue_codes(publication), ("delivery-payload-malformed",))

    def test_repeated_contract_publication_serialization_is_stable(self):
        source_delivery_result = delivery_result()
        publisher = WebsiteProjectionDeliveryContractPublisher()

        first = publisher.publish(source_delivery_result)
        second = publisher.publish(source_delivery_result)

        self.assertEqual(
            first.contract_instance.serialize(),
            second.contract_instance.serialize(),
        )

    def test_delivery_omits_dashboard_content_when_not_explicitly_supplied(self):
        payload = delivery_result().delivery.to_dict()

        self.assertNotIn("dashboardContent", payload)
        self.assertNotIn("renderingGuidance", payload)

    def test_delivery_preserves_explicit_dashboard_content(self):
        result = delivery_result_with_content()

        self.assertTrue(result.delivered)
        payload = result.delivery.to_dict()

        self.assertEqual(
            payload["dashboardContent"],
            approved_dashboard_content().to_dict(),
        )
        self.assertEqual(
            payload["dashboardContent"]["summaries"]["items"][0]["summary"],
            "Approved projection content supplied by EIP.",
        )

    def test_delivery_preserves_explicit_rendering_guidance(self):
        result = delivery_result_with_content()

        self.assertTrue(result.delivered)
        payload = result.delivery.to_dict()

        self.assertEqual(
            payload["renderingGuidance"],
            approved_rendering_guidance().to_dict(),
        )
        self.assertEqual(
            payload["renderingGuidance"]["sectionOrder"],
            ["summaries", "metrics"],
        )

    def test_published_contract_preserves_dashboard_content_and_guidance(self):
        source_delivery_result = delivery_result_with_content()

        publication = published_contract_instance(source_delivery_result)
        contract_payload = publication.contract_instance.to_dict()
        delivery_payload = source_delivery_result.delivery.to_dict()

        self.assertTrue(publication.published)
        self.assertEqual(
            contract_payload["dashboardContent"],
            delivery_payload["dashboardContent"],
        )
        self.assertEqual(
            contract_payload["renderingGuidance"],
            delivery_payload["renderingGuidance"],
        )

    def test_optional_content_preserves_contract_identity_and_governance(self):
        publication = published_contract_instance(delivery_result_with_content())
        payload = publication.contract_instance.to_dict()

        self.assertEqual(
            payload["deliveryMetadata"]["deliveryContractVersion"],
            WEBSITE_PROJECTION_DELIVERY_CONTRACT_VERSION,
        )
        self.assertEqual(
            payload["deliveryMetadata"]["publicationPolicyVersion"],
            WEBSITE_PROJECTION_DELIVERY_PUBLICATION_POLICY_VERSION,
        )
        self.assertEqual(
            payload["eligibility"]["compatibilityState"],
            "compatible",
        )
        self.assertEqual(
            payload["compatibility"]["deliveryContractCompatibility"],
            "compatible",
        )
        self.assertEqual(
            payload["limitations"]["limitationVisibilityState"],
            "visible",
        )
        self.assertIn(
            {
                "fieldGroup": "dashboardContent",
                "classification": "restricted_assessment",
            },
            payload["classification"]["fieldClassifications"],
        )

    def test_optional_content_models_are_immutable(self):
        dashboard_content = approved_dashboard_content()
        rendering_guidance = approved_rendering_guidance()

        with self.assertRaises(FrozenInstanceError):
            dashboard_content.sections = ()

        with self.assertRaises(FrozenInstanceError):
            dashboard_content.sections[0][1].items[0].label = "changed"

        with self.assertRaises(FrozenInstanceError):
            rendering_guidance.section_order = ("metrics",)

    def test_optional_content_serialization_is_deterministic(self):
        publication = published_contract_instance(delivery_result_with_content())

        first = publication.contract_instance.serialize()
        second = publication.contract_instance.serialize()

        self.assertEqual(first, second)
        self.assertEqual(json.loads(first), publication.contract_instance.to_dict())

    def test_optional_content_publication_is_stable_repeatedly(self):
        source_delivery_result = delivery_result_with_content()
        publisher = WebsiteProjectionDeliveryContractPublisher()

        first = publisher.publish(source_delivery_result)
        second = publisher.publish(source_delivery_result)

        self.assertEqual(first, second)
        self.assertEqual(
            first.contract_instance.serialize(),
            second.contract_instance.serialize(),
        )

    def test_dashboard_content_requires_approved_classification(self):
        result = delivery_result(
            WebsiteProjectionDeliveryRequest(
                dashboard_content=approved_dashboard_content(),
            )
        )

        self.assertFalse(result.delivered)
        self.assertIsNone(result.delivery)
        self.assertEqual(issue_codes(result), ("classification-not-approved",))

    def test_rendering_guidance_requires_approved_classification(self):
        result = delivery_result(
            WebsiteProjectionDeliveryRequest(
                rendering_guidance=approved_rendering_guidance(),
            )
        )

        self.assertFalse(result.delivered)
        self.assertIsNone(result.delivery)
        self.assertEqual(issue_codes(result), ("classification-not-approved",))

    def test_malformed_dashboard_content_fails_closed(self):
        result = delivery_result(
            WebsiteProjectionDeliveryRequest(
                field_classifications=APPROVED_FIELD_CLASSIFICATIONS,
                dashboard_content=WebsiteProjectionDashboardContent(
                    sections=()
                ),
            )
        )

        self.assertFalse(result.delivered)
        self.assertIsNone(result.delivery)
        self.assertEqual(issue_codes(result), ("delivery-payload-malformed",))

    def test_malformed_rendering_guidance_fails_closed(self):
        result = delivery_result(
            WebsiteProjectionDeliveryRequest(
                field_classifications=APPROVED_FIELD_CLASSIFICATIONS,
                rendering_guidance=WebsiteProjectionRenderingGuidance(
                    section_order=("summaries", "summaries"),
                ),
            )
        )

        self.assertFalse(result.delivered)
        self.assertIsNone(result.delivery)
        self.assertEqual(issue_codes(result), ("delivery-payload-malformed",))

    def test_optional_content_does_not_generate_business_semantics(self):
        payload = delivery_result().delivery.to_dict()

        generated_content_keys = (
            "dashboardContent",
            "renderingGuidance",
            "readiness",
            "confidence",
            "recommendations",
            "priorities",
            "narrative",
        )
        for key in generated_content_keys:
            self.assertFalse(contains_key(payload, key), key)

    def test_rejects_serialized_prohibited_artifacts_in_dashboard_text(self):
        projection = executive_projection()
        cases = (
            ("source package", '{"sourcePackage":{"marker":"test"}}'),
            ("derived artifact", '{"sourceDerivedArtifact":{"marker":"test"}}'),
            ("nested object", '{"allowed":{"sourcePackage":{}}}'),
            ("nested array", '[{"allowed":{"sourceDerivedArtifact":{}}}]'),
            (
                "multiple levels",
                '{"allowed":[{"deeper":[{"sourcePackage":{}}]}]}',
            ),
            ("surrounding whitespace", ' \n {"sourcePackage":{}} \t '),
            ("Unicode escaped key", r'{"source\u0050ackage":{}}'),
            ("JSON escaped key", r'{"\u0073ourcePackage":{}}'),
            ("serialized projection", json.dumps(projection.to_dict())),
        )
        publisher = WebsiteProjectionDeliveryPublisher()
        for name, value in cases:
            with self.subTest(name=name):
                request = dashboard_text_request(value)
                before_request = request.to_dict()
                before_projection = projection.to_dict()

                result = publisher.publish(request, projection)

                self.assertFalse(result.delivered)
                self.assertIsNone(result.delivery)
                self.assertEqual(issue_codes(result), ("prohibited-field-present",))
                self.assertEqual(request.to_dict(), before_request)
                self.assertEqual(projection.to_dict(), before_projection)

    def test_rejects_serialized_json_candidates_exceeding_parse_limits(self):
        oversized = '{"allowed":"' + "x" * _MAX_SERIALIZED_JSON_CANDIDATE_CHARS + '"}'
        deeply_nested = "[" * (_MAX_SERIALIZED_JSON_CONTAINER_DEPTH + 2)
        deeply_nested += "0" + "]" * (_MAX_SERIALIZED_JSON_CONTAINER_DEPTH + 2)
        projection = executive_projection()
        for name, value in (("oversized", oversized), ("deep", deeply_nested)):
            with self.subTest(name=name):
                request = dashboard_text_request(value)
                before = request.to_dict()

                result = WebsiteProjectionDeliveryPublisher().publish(
                    request, projection
                )

                self.assertFalse(result.delivered)
                self.assertIsNone(result.delivery)
                self.assertEqual(issue_codes(result), ("delivery-payload-malformed",))
                self.assertEqual(request.to_dict(), before)

        request = dashboard_text_request('{"allowed":true}')
        before = request.to_dict()
        with patch(
            "executive_intelligence_platform.projection_delivery.delivery.json.loads",
            side_effect=RecursionError,
        ):
            result = WebsiteProjectionDeliveryPublisher().publish(request, projection)
        self.assertFalse(result.delivered)
        self.assertIsNone(result.delivery)
        self.assertEqual(issue_codes(result), ("delivery-payload-malformed",))
        self.assertEqual(request.to_dict(), before)

    def test_existing_scanner_still_finds_raw_nested_keys(self):
        self.assertEqual(
            _find_prohibited_key({"outer": {"sourcePackage": {}}}),
            "$.outer.sourcePackage",
        )
        self.assertEqual(
            _find_prohibited_key({"outer": [{"sourceDerivedArtifact": {}}]}),
            "$.outer[0].sourceDerivedArtifact",
        )

    def test_allows_narrative_and_harmless_json_without_changing_text(self):
        cases = (
            "The executive summary describes the current position.",
            "The finding identifies a governance gap.",
            "The recommendation addresses the source gap.",
            "Risk remains high; next steps are clear.",
            "The draft uses {braces} and punctuation: commas, semicolons; and periods.",
            'The word "sourcePackage" appears in a quoted example.',
            '{"example":"safe"}',
            '{"allowed":{"nested":"safe"}}',
            '[{"allowed":{"nested":"safe"}}]',
            "Executive narrative. " * 4000,
            '{"sourcePackage": not valid JSON}',
            '{"sourcePackage":{}} followed by prose',
            json.dumps('{"sourcePackage":{}}'),
            json.dumps({"allowed": json.dumps({"sourcePackage": {}})}),
        )
        publisher = WebsiteProjectionDeliveryPublisher()
        projection = executive_projection()
        for value in cases:
            with self.subTest(value=value[:80]):
                request = dashboard_text_request(value)
                before = request.to_dict()

                first = publisher.publish(request, projection)
                second = publisher.publish(request, projection)

                self.assertTrue(first.delivered, first.issues)
                self.assertEqual(first.issues, ())
                self.assertEqual(first.to_dict(), second.to_dict())
                serialized = first.delivery.to_dict()
                self.assertEqual(
                    serialized["dashboardContent"]["summaries"]["items"][0][
                        "fields"
                    ][0]["value"],
                    value,
                )
                serialized["dashboardContent"]["summaries"]["items"][0][
                    "fields"
                ][0]["value"] = "changed"
                self.assertEqual(first.delivery.to_dict(), second.delivery.to_dict())
                self.assertEqual(request.to_dict(), before)


if __name__ == "__main__":
    unittest.main()
