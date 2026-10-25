"""Frozen Assessment Service v2 fixture through EIP projection delivery."""

import copy
import json
import sys
import unittest
from dataclasses import replace
from pathlib import Path


EIP_ROOT = Path(__file__).resolve().parents[2]
ASSESSMENT_SERVICE_ROOT = EIP_ROOT.parent / "nguyen-ai-assessment-service"
sys.path.insert(0, str(EIP_ROOT / "src"))
sys.path.insert(0, str(ASSESSMENT_SERVICE_ROOT / "src"))
sys.path.insert(0, str(ASSESSMENT_SERVICE_ROOT / "tests"))

from assessment.executive_snapshot_handoff import (  # noqa: E402
    produce_executive_assessment_snapshot,
)
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


def governed_delivery_pipeline():
    production = produce_executive_assessment_snapshot(
        golden_fixture_request(75, "mixed-strong", "two-high")
    )
    if not production.is_success:
        raise AssertionError(production.failure)
    snapshot = production.serialized_snapshot
    compatibility = validate_snapshot_compatibility(snapshot)
    catalog = SnapshotCatalog()
    admission = catalog.admit(
        snapshot, producer_snapshot_identity="fixture-v1-high-concentration-risk"
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
    return snapshot, compatibility, admission, derivation, package, projection, delivery


def issue_codes(result):
    return tuple(issue.code for issue in result.issues)


class FrozenAssessmentServiceProjectionDeliveryTests(unittest.TestCase):
    def test_frozen_v2_fixture_reaches_metadata_only_delivery(self):
        snapshot, compatibility, admission, derivation, package, projection, delivery = (
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
        snapshot, _compatibility, admission, derivation, package, projection, delivery = (
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
        _snapshot, _compatibility, _admission, derivation, package, projection, _delivery = (
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
        _snapshot, _compatibility, _admission, _derivation, package, projection, _delivery = (
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
