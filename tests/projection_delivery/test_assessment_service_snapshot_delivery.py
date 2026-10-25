"""Frozen Assessment Service v2 fixture through EIP projection delivery."""

import copy
import json
import sys
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

EIP_ROOT = Path(__file__).resolve().parents[2]
ASSESSMENT_SERVICE_ROOT = EIP_ROOT.parent / "nguyen-ai-assessment-service"
sys.path.insert(0, str(EIP_ROOT / "src"))
sys.path.insert(0, str(ASSESSMENT_SERVICE_ROOT / "src"))
sys.path.insert(0, str(ASSESSMENT_SERVICE_ROOT / "tests"))

from assessment.executive_snapshot_handoff import (  # noqa: E402
    produce_executive_assessment_snapshot,
)
from assessment.producer_snapshot_attestation import ProducerSnapshotIssuer  # noqa: E402
from test_golden_fixture_regression import request as golden_fixture_request  # noqa: E402
from executive_intelligence_platform.executive_intelligence_package import (  # noqa: E402
    ExecutiveIntelligencePackageAssembler,
    ExecutiveIntelligencePackageRequest,
)
from executive_intelligence_platform.executive_intelligence_projection import (  # noqa: E402
    ExecutiveIntelligenceProjectionProjector,
    ExecutiveIntelligenceProjectionRequest,
)
from executive_intelligence_platform.projection_delivery import (  # noqa: E402
    WEBSITE_PROJECTION_DELIVERY_CONTRACT_VERSION,
    WEBSITE_PROJECTION_DELIVERY_PUBLICATION_POLICY_VERSION,
    WebsiteProjectionDeliveryContractPublisher,
    WebsiteProjectionDeliveryPublisher,
    WebsiteProjectionDeliveryRequest,
)
from executive_intelligence_platform.snapshot_catalog import SnapshotCatalog  # noqa: E402
from executive_intelligence_platform.snapshot_compatibility import (  # noqa: E402
    validate_snapshot_compatibility,
)
from executive_intelligence_platform.snapshot_derivation import (  # noqa: E402
    SnapshotDerivationRequest,
    SnapshotDerivationRuntime,
)
from executive_intelligence_platform.snapshot_derivation.derivation import (  # noqa: E402
    GOVERNED_CONTENT_DERIVATION_RULE_VERSION,
)
from executive_intelligence_platform.projection_delivery.delivery import (  # noqa: E402
    _publish_governed_dashboard_content,
    WebsiteProjectionContentItem,
    WebsiteProjectionContentSection,
    WebsiteProjectionDashboardContent,
    WebsiteProjectionDisplayField,
)
from executive_intelligence_platform.projection_delivery.verified_admission import (  # noqa: E402
    VerifiedSnapshotGateway,
)


def governed_delivery_pipeline(finding_profile="two-high"):
    production = produce_executive_assessment_snapshot(
        golden_fixture_request(75, "mixed-strong", finding_profile)
    )
    if not production.is_success:
        raise AssertionError(production.failure)
    snapshot = production.serialized_snapshot
    raw = json.dumps(snapshot, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    signing_key = Ed25519PrivateKey.generate()
    sidecar = ProducerSnapshotIssuer(
        signing_key, issuer_id="nguyen-ai-assessment",
        key_id="phase1g-test-ephemeral",
        producer_release_commit="a075a679a053ee9d0eb9a32d7f0ffa2dc796f0da",
    ).issue(raw)
    gateway = VerifiedSnapshotGateway(
        trusted_issuer_id="nguyen-ai-assessment",
        trusted_key_id="phase1g-test-ephemeral",
        trusted_public_key=signing_key.public_key(),
        expected_release_commit="a075a679a053ee9d0eb9a32d7f0ffa2dc796f0da",
    )
    verified_admission = gateway.admit(raw, sidecar)
    compatibility = validate_snapshot_compatibility(snapshot)
    catalog = SnapshotCatalog()
    admission = catalog.admit(
        snapshot, producer_snapshot_identity=sidecar["producerSnapshotIdentity"]
    )
    if not admission.accepted:
        raise AssertionError(admission.issues)
    derivation = SnapshotDerivationRuntime().derive(
        admission.entry,
        SnapshotDerivationRequest(GOVERNED_CONTENT_DERIVATION_RULE_VERSION),
    )
    if not derivation.derived:
        raise AssertionError(derivation.issues)
    package = ExecutiveIntelligencePackageAssembler().assemble(
        ExecutiveIntelligencePackageRequest(), derivation.artifact
    )
    if not package.packaged:
        raise AssertionError(package.issues)
    projection = ExecutiveIntelligenceProjectionProjector().project(
        ExecutiveIntelligenceProjectionRequest(), package.package
    )
    if not projection.projected:
        raise AssertionError(projection.issues)
    delivery = WebsiteProjectionDeliveryPublisher().publish(
        WebsiteProjectionDeliveryRequest(), projection.projection
    )
    return (snapshot, compatibility, admission, derivation, package, projection,
            delivery, gateway, verified_admission)


def issue_codes(result):
    return tuple(issue.code for issue in result.issues)


class FrozenAssessmentServiceProjectionDeliveryTests(unittest.TestCase):
    def test_governed_dashboard_omits_empty_findings_section(self):
        snapshot, _compatibility, _admission, _derivation, _package, projection, _, gateway, verified = (
            governed_delivery_pipeline("none")
        )
        self.assertEqual(
            snapshot["businessDecisionPackage"]["governedConclusions"]
            ["severityAssignedFindings"], []
        )
        result = _publish_governed_dashboard_content(
            WebsiteProjectionDeliveryRequest(), projection.projection,
            verified_admission=verified, trusted_gateway=gateway,
        )
        self.assertTrue(result.delivered, result.issues)
        self.assertNotIn("findings", result.delivery.to_dict()["dashboardContent"])

    def test_governed_dashboard_opt_in_copies_frozen_conclusions(self):
        snapshot, compatibility, admission, derivation, package, projection, ordinary, gateway, verified = (
            governed_delivery_pipeline()
        )
        self.assertTrue(all((compatibility.is_valid, admission.accepted,
                             derivation.derived, package.packaged,
                             projection.projected, ordinary.delivered)))
        governed = snapshot["businessDecisionPackage"]["governedConclusions"]
        request = WebsiteProjectionDeliveryRequest()
        before_request = request.to_dict()
        before_projection = projection.projection.to_dict()
        first = _publish_governed_dashboard_content(
            request, projection.projection,
            verified_admission=verified, trusted_gateway=gateway,
        )
        second = _publish_governed_dashboard_content(
            request, projection.projection,
            verified_admission=verified, trusted_gateway=gateway,
        )
        self.assertTrue(first.delivered, first.issues)
        self.assertEqual(first.issues, ())
        self.assertEqual(first.to_dict(), second.to_dict())
        payload = first.delivery.to_dict()
        content = payload["dashboardContent"]
        self.assertEqual(tuple(content), (
            "summaries", "metrics", "findings", "risks", "recommendations"
        ))
        self.assertNotIn("decisions", content)
        self.assertEqual(tuple(len(section["items"]) for section in content.values()),
                         (7, 1, 2, 1, 2))
        self.assertEqual(sum(len(section["items"]) for section in content.values()), 13)
        self.assertEqual(
            [(item["fields"][0]["value"], item["summary"])
             for item in content["summaries"]["items"]],
            list(governed["executiveSummary"]["sectionText"].items()),
        )
        self.assertEqual(
            [(item["label"], [field["value"] for field in item["fields"]])
             for item in content["findings"]["items"]],
            [(finding["title"], [finding["findingId"],
               finding["sequenceIdentifier"], finding["severityClassification"]])
             for finding in governed["severityAssignedFindings"]],
        )
        self.assertEqual(
            content["risks"]["items"][0]["fields"][0]["value"],
            governed["assessmentRisk"]["riskClassification"],
        )
        self.assertEqual(
            content["metrics"]["items"][0]["fields"][0]["value"],
            governed["confidence"]["confidenceClassification"],
        )
        self.assertEqual(
            [[field["value"] for field in item["fields"]]
             for item in content["recommendations"]["items"]],
            [[item["findingId"], item["recommendationClassification"]]
            for item in governed["recommendations"]],
        )
        self.assertEqual(payload["classification"]["responseClassification"],
                         "restricted_assessment")
        self.assertIn(
            {"fieldGroup": "dashboardContent", "classification": "restricted_assessment"},
            payload["classification"]["fieldClassifications"],
        )
        self.assertNotIn("delivery-contract-exposes-projection-metadata-and-lineage-only",
                         payload["limitations"]["limitationIndicators"])
        self.assertEqual(payload["versionContext"],
                         ordinary.delivery.to_dict()["versionContext"])
        self.assertEqual(payload["lineage"], ordinary.delivery.to_dict()["lineage"])
        self.assertEqual(payload["lineage"]["snapshot"]["productionAuthority"],
                         "NOT_PRODUCTION_AUTHORITATIVE")
        serialized = json.dumps(content)
        for excluded in ("sourceReferences", "sourcePackage", "sourceDerivedArtifact",
                         "decisionEvaluation", "rawEvidence"):
            self.assertNotIn(excluded, serialized)
        payload["dashboardContent"]["summaries"]["items"][0]["summary"] = "changed"
        self.assertEqual(first.delivery.to_dict(), second.delivery.to_dict())
        self.assertEqual(request.to_dict(), before_request)
        self.assertEqual(projection.projection.to_dict(), before_projection)
        self.assertNotIn("dashboardContent", ordinary.delivery.to_dict())

    def test_governed_dashboard_opt_in_rejects_invalid_upstream_artifacts(self):
        _snapshot, _compatibility, _admission, derivation, package, projection, _, gateway, verified = (
            governed_delivery_pipeline()
        )
        artifact = derivation.artifact

        def altered(change):
            conclusions = copy.deepcopy(artifact.to_dict()["governedConclusions"])
            change(conclusions)
            return replace(artifact, governed_conclusions=conclusions)

        missing = replace(artifact)
        object.__setattr__(missing, "governed_conclusions", None)
        cases = (
            missing,
            altered(lambda c: c["severityAssignedFindings"][0].__setitem__(
                "severityClassification", "unsupported")),
            altered(lambda c: c["assessmentRisk"].__setitem__(
                "riskClassification", "moderate-risk")),
            altered(lambda c: c["severityAssignedFindings"].reverse()),
            altered(lambda c: c["recommendations"].reverse()),
            altered(lambda c: c["executiveSummary"]["sectionText"].pop(
                "closing-assessment-statement")),
            replace(artifact, producer_snapshot_identity="wrong-snapshot"),
        )
        request = WebsiteProjectionDeliveryRequest()
        for index, invalid in enumerate(cases):
            with self.subTest(case=index):
                forged = replace(projection.projection, source_package=replace(
                    package.package, source_derived_artifact=invalid
                ))
                before = forged.to_dict()
                result = _publish_governed_dashboard_content(
                    request, forged,
                    verified_admission=verified, trusted_gateway=gateway,
                )
                self.assertFalse(result.delivered)
                self.assertIsNone(result.delivery)
                self.assertEqual(issue_codes(result), (
                    "verified-admission-invalid" if index == 2 else
                    "upstream-projection-unavailable",
                ))
                self.assertEqual(forged.to_dict(), before)

    def test_governed_dashboard_opt_in_rejects_classification_and_generated_content(self):
        _snapshot, _compatibility, _admission, _derivation, _package, projection, _, gateway, verified = (
            governed_delivery_pipeline()
        )
        request = WebsiteProjectionDeliveryRequest(field_classifications=(
            *WebsiteProjectionDeliveryRequest().field_classifications,
            ("dashboardContent", "public"),
        ))
        result = _publish_governed_dashboard_content(
            request, projection.projection,
            verified_admission=verified, trusted_gateway=gateway,
        )
        self.assertFalse(result.delivered)
        self.assertIsNone(result.delivery)
        self.assertEqual(issue_codes(result), ("classification-not-approved",))

        invalid = WebsiteProjectionDashboardContent(sections=((
            "summaries", WebsiteProjectionContentSection(
                label="Executive Summary", items=(WebsiteProjectionContentItem(
                    label="invalid", fields=(),
                ),),
            ),
        ),))
        leaked = WebsiteProjectionDashboardContent(sections=((
            "summaries", WebsiteProjectionContentSection(
                label="Executive Summary", items=(WebsiteProjectionContentItem(
                    label="invalid", fields=(WebsiteProjectionDisplayField(
                        "text", '{"sourcePackage":{"marker":"safe-test"}}'
                    ),),
                ),),
            ),
        ),))
        for generated, code in ((invalid, "delivery-payload-malformed"),
                                (leaked, "prohibited-field-present")):
            with self.subTest(code=code):
                with patch(
                    "executive_intelligence_platform.projection_delivery.delivery._map_governed_dashboard_content",
                    return_value=generated,
                ):
                    result = _publish_governed_dashboard_content(
                        WebsiteProjectionDeliveryRequest(), projection.projection,
                        verified_admission=verified, trusted_gateway=gateway,
                    )
                self.assertFalse(result.delivered)
                self.assertIsNone(result.delivery)
                self.assertEqual(issue_codes(result), (code,))

    def test_frozen_v2_fixture_reaches_metadata_only_delivery(self):
        snapshot, compatibility, admission, derivation, package, projection, delivery, _gateway, _verified = (
            governed_delivery_pipeline()
        )
        self.assertTrue(compatibility.is_valid)
        self.assertTrue(admission.accepted)
        self.assertTrue(derivation.derived)
        self.assertTrue(package.packaged)
        self.assertTrue(projection.projected)
        self.assertTrue(delivery.delivered, delivery.issues)
        self.assertEqual(delivery.issues, ())
        self.assertIs(projection.projection.source_package, package.package)

        payload = delivery.delivery.to_dict()
        self.assertEqual(
            tuple(payload),
            (
                "deliveryMetadata", "projectionReference", "publication",
                "eligibility", "compatibility", "versionContext", "lineage",
                "classification", "limitations",
            ),
        )
        self.assertEqual(
            payload["deliveryMetadata"]["deliveryContractVersion"],
            WEBSITE_PROJECTION_DELIVERY_CONTRACT_VERSION,
        )
        self.assertEqual(
            payload["deliveryMetadata"]["publicationPolicyVersion"],
            WEBSITE_PROJECTION_DELIVERY_PUBLICATION_POLICY_VERSION,
        )
        producer_versions = snapshot["businessDecisionPackage"]["versionMetadata"]
        context = payload["versionContext"]
        self.assertEqual(
            context["businessDecisionPackageContractVersion"],
            producer_versions["contractVersion"],
        )
        self.assertEqual(
            context["assessmentVersion"], producer_versions["assessmentVersion"]
        )
        self.assertEqual(
            context["methodologyVersion"], producer_versions["methodologyVersion"]
        )
        self.assertEqual(
            context["derivationRuleVersion"],
            GOVERNED_CONTENT_DERIVATION_RULE_VERSION,
        )
        self.assertEqual(
            context["componentVersionReferences"],
            list(admission.entry.admission_metadata.source_component_ids),
        )
        self.assertEqual(
            payload["projectionReference"]["producerSnapshotIdentity"],
            admission.entry.admission_metadata.producer_snapshot_identity,
        )
        self.assertEqual(
            payload["lineage"]["snapshot"]["productionAuthority"],
            "NOT_PRODUCTION_AUTHORITATIVE",
        )
        self.assertEqual(
            payload["lineage"]["assessmentServiceProvenance"]["productionAuthority"],
            "NOT_PRODUCTION_AUTHORITATIVE",
        )
        self.assertNotIn("dashboardContent", payload)
        self.assertNotIn("renderingGuidance", payload)
        serialized = json.dumps(payload)
        self.assertNotIn("governedConclusions", serialized)
        self.assertNotIn("sourcePackage", serialized)
        self.assertNotIn("sourceDerivedArtifact", serialized)

        publication = WebsiteProjectionDeliveryContractPublisher().publish(delivery)
        self.assertTrue(publication.published)
        self.assertEqual(publication.contract_instance.to_dict(), payload)

    def test_frozen_v2_delivery_is_deterministic_and_immutable(self):
        snapshot, _compatibility, admission, derivation, package, projection, delivery, _gateway, _verified = (
            governed_delivery_pipeline()
        )
        before_snapshot = copy.deepcopy(snapshot)
        before_entry = admission.entry.to_dict()
        before_artifact = derivation.artifact.to_dict()
        before_package = package.package.to_dict()
        before_projection = projection.projection.to_dict()
        publisher = WebsiteProjectionDeliveryPublisher()
        repeated = publisher.publish(
            WebsiteProjectionDeliveryRequest(), projection.projection
        )
        self.assertEqual(delivery.to_dict(), repeated.to_dict())
        before_delivery = delivery.delivery.to_dict()
        changed = delivery.delivery.to_dict()
        changed["versionContext"]["assessmentVersion"] = "changed"
        self.assertEqual(delivery.delivery.to_dict(), before_delivery)
        self.assertEqual(projection.projection.to_dict(), before_projection)
        self.assertEqual(package.package.to_dict(), before_package)
        self.assertEqual(derivation.artifact.to_dict(), before_artifact)
        self.assertEqual(admission.entry.to_dict(), before_entry)
        self.assertEqual(snapshot, before_snapshot)

    def test_frozen_v2_delivery_rejects_invalid_embedded_artifacts(self):
        _snapshot, _compatibility, _admission, derivation, package, projection, _delivery, _gateway, _verified = (
            governed_delivery_pipeline()
        )
        artifact = derivation.artifact

        def changed_conclusions(change):
            content = copy.deepcopy(artifact.to_dict()["governedConclusions"])
            change(content)
            return replace(artifact, governed_conclusions=content)

        missing = replace(artifact)
        object.__setattr__(missing, "governed_conclusions", None)
        unsupported_rule = replace(artifact)
        object.__setattr__(
            unsupported_rule, "derivation_rule_version", "unsupported-rule"
        )
        cases = (
            (
                "malformed conclusions",
                changed_conclusions(lambda c: c.__setitem__("confidence", {})),
            ),
            ("missing conclusions", missing),
            (
                "missing source references",
                changed_conclusions(
                    lambda c: c["severityAssignedFindings"][0].__setitem__(
                        "sourceReferences", []
                    )
                ),
            ),
            (
                "finding order",
                changed_conclusions(
                    lambda c: c["severityAssignedFindings"].reverse()
                ),
            ),
            ("unsupported derivation rule", unsupported_rule),
            (
                "unsupported producer package",
                replace(
                    artifact,
                    catalog_admission_metadata=replace(
                        artifact.catalog_admission_metadata,
                        package_contract_version="business-decision-package-v3",
                    ),
                ),
            ),
            (
                "conflicting assessment",
                replace(artifact, assessment_version="conflicting-assessment"),
            ),
            (
                "conflicting methodology",
                replace(artifact, methodology_version="conflicting-methodology"),
            ),
            (
                "conflicting source components",
                replace(
                    artifact,
                    producer_provenance=replace(
                        artifact.producer_provenance,
                        source_component_ids=("decisionEvaluation",),
                    ),
                ),
            ),
            (
                "conflicting snapshot lineage",
                replace(artifact, producer_snapshot_identity="different-snapshot"),
            ),
            (
                "invalid authority",
                replace(
                    artifact,
                    catalog_admission_metadata=replace(
                        artifact.catalog_admission_metadata,
                        production_authority="UPGRADED",
                    ),
                    producer_provenance=replace(
                        artifact.producer_provenance,
                        production_authority="UPGRADED",
                    ),
                ),
            ),
        )
        projector = ExecutiveIntelligenceProjectionProjector()
        publisher = WebsiteProjectionDeliveryPublisher()
        original = projection.projection.to_dict()
        for name, invalid in cases:
            with self.subTest(name=name):
                forged_package = replace(
                    package.package, source_derived_artifact=invalid
                )
                forged_projection = replace(
                    projection.projection, source_package=forged_package
                )
                before = forged_projection.to_dict()
                rejected = projector.project(
                    ExecutiveIntelligenceProjectionRequest(), forged_package
                )
                self.assertFalse(rejected.projected)
                result = publisher.publish(
                    WebsiteProjectionDeliveryRequest(), forged_projection
                )
                self.assertFalse(result.delivered)
                self.assertIsNone(result.delivery)
                self.assertEqual(
                    issue_codes(result), ("upstream-projection-unavailable",)
                )
                self.assertEqual(forged_projection.to_dict(), before)
        self.assertEqual(projection.projection.to_dict(), original)

    def test_frozen_v2_delivery_rejects_package_and_projection_conflicts(self):
        _snapshot, _compatibility, _admission, _derivation, package, projection, _delivery, _gateway, _verified = (
            governed_delivery_pipeline()
        )
        original = projection.projection
        invalid_package = replace(
            package.package,
            assessment_version="conflicting-assessment",
            lineage=replace(
                package.package.lineage, assessment_version="conflicting-assessment"
            ),
        )
        cases = (
            (
                "invalid package metadata",
                replace(original, source_package=invalid_package),
                "upstream-projection-unavailable",
            ),
            (
                "conflicting projection metadata",
                replace(
                    original,
                    assessment_version="conflicting-assessment",
                    lineage=replace(
                        original.lineage, assessment_version="conflicting-assessment"
                    ),
                ),
                "lineage-state-incomplete",
            ),
            (
                "conflicting projection rule lineage",
                replace(
                    original,
                    lineage=replace(
                        original.lineage,
                        projection_rule_version="unsupported-projection-rule",
                    ),
                ),
                "lineage-state-incomplete",
            ),
        )
        for name, forged, expected_issue in cases:
            with self.subTest(name=name):
                before = forged.to_dict()
                result = WebsiteProjectionDeliveryPublisher().publish(
                    WebsiteProjectionDeliveryRequest(), forged
                )
                self.assertFalse(result.delivered)
                self.assertIsNone(result.delivery)
                self.assertEqual(issue_codes(result), (expected_issue,))
                self.assertEqual(forged.to_dict(), before)


if __name__ == "__main__":
    unittest.main()
