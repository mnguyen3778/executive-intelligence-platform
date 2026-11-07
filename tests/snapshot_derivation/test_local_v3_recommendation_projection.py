"""Synthetic, local-only verification of producer-owned v3 action projection."""

import copy
import sys
import unittest
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
from unittest.mock import patch


EIP_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(EIP_ROOT / "src"))
sys.path.insert(0, str(EIP_ROOT / "tests" / "projection_delivery"))

import test_local_v3_admission as fixtures  # noqa: E402
from executive_intelligence_platform.projection_delivery.verified_admission import (  # noqa: E402
    LocalV3GovernedProjection, VerifiedAdmissionError, VerifiedSnapshotGateway,
)
from executive_intelligence_platform.snapshot_derivation.local_v3_recommendation_projection import (  # noqa: E402
    LocalV3RecommendationProjection, project_local_v3_recommendations,
)


class LocalV3RecommendationProjectionTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.LocalV3AdmissionTests(
            methodName="test_selection_and_cross_version_evidence_fail_closed"
        )
        self.fixture.setUp()
        self.gateway = self.fixture.gateway
        self.produced, self.raw = self.fixture.produced_v3(
            fixtures.request(75, "mixed-strong", "two-high")
        )
        self.admission = self.gateway.admit_local_v3(
            self.raw, self.produced.attestation_sidecar,
            package_contract_version=fixtures.V3,
        )

    def project(self, admission=None, gateway=None, version=fixtures.V3):
        return project_local_v3_recommendations(
            self.gateway if gateway is None else gateway,
            self.admission if admission is None else admission,
            package_contract_version=version,
        )

    def rejected(self, operation):
        with self.assertRaises(VerifiedAdmissionError):
            operation()

    def altered_admission(self, edit):
        altered = copy.deepcopy(self.produced.serialized_snapshot)
        edit(altered)
        return replace(self.admission, _snapshot_bytes=fixtures.encode(altered))

    def test_preserves_all_eight_producer_rules_and_exact_order(self):
        cases = [
            fixtures.request(75, "adequate", "critical"),
            fixtures.request(75, "mixed-strong", "two-high"),
            fixtures.request(50, "adequate", "medium"),
            fixtures.request(50, "adequate", "low"),
            fixtures.request(100, "strong", "strength"),
            fixtures.request(50, "adequate", "none"),
        ]
        for kind, basis in (("Observation", "observation"),
                            ("Opportunity", "opportunity")):
            finding = fixtures.FindingInput(
                "finding-local-" + kind.lower(), "Local finding", "POC", (),
                "fixture-input", kind, basis, ("fixture-input",),
            )
            cases.append(replace(fixtures.request(50, "adequate", "none"),
                                 findings=(finding,)))

        seen = set()
        for canonical in cases:
            with self.subTest(findings=canonical.findings):
                produced, raw = self.fixture.produced_v3(canonical)
                admission = self.gateway.admit_local_v3(
                    raw, produced.attestation_sidecar,
                    package_contract_version=fixtures.V3,
                )
                projection = self.project(admission)
                source = produced.serialized_snapshot["businessDecisionPackage"]
                rows = source["governedConclusions"]["recommendations"]
                self.assertEqual(len(projection.recommendations), len(rows))
                self.assertEqual(projection.package_contract_version, fixtures.V3)
                self.assertEqual(
                    projection.methodology_version,
                    source["versionMetadata"]["methodologyVersion"],
                )
                self.assertEqual(projection.verification_evidence, admission.evidence)
                self.assertEqual(projection.producer_snapshot_identity,
                                 admission.evidence.producer_snapshot_identity)
                self.assertFalse(projection.release_eligible)
                for item, row in zip(projection.recommendations, rows):
                    self.assertEqual(
                        (item.finding_id, item.recommendation_classification,
                         item.recommendation_decision_identifier,
                         item.recommendation_decision_table_version,
                         item.recommendation_action_text),
                        tuple(row.values()),
                    )
                    self.assertEqual(item.recommendation_action_text,
                                     fixtures.APPROVED_RECOMMENDATION_ACTION_TEXT_BY_RULE[
                                         item.recommendation_decision_identifier])
                    seen.add(item.recommendation_decision_identifier)
                if not canonical.findings:
                    self.assertEqual(len(projection.recommendations), 1)
                    self.assertIsNone(projection.recommendations[0].finding_id)
        self.assertEqual(seen, set(fixtures.APPROVED_RECOMMENDATION_ACTION_TEXT_BY_RULE))

    def test_reverifies_through_same_gateway_without_publication(self):
        with patch.object(self.gateway, "deliver_local_v3",
                          wraps=self.gateway.deliver_local_v3) as deliver, patch(
            "executive_intelligence_platform.projection_delivery.delivery."
            "WebsiteProjectionDeliveryContractPublisher.publish",
            side_effect=AssertionError("downstream publication invoked"),
        ) as publish:
            projected = self.project()
        self.assertIsInstance(projected, LocalV3RecommendationProjection)
        deliver.assert_called_once_with(
            self.admission, package_contract_version=fixtures.V3,
        )
        publish.assert_not_called()

    def test_immutable_internal_result_does_not_expose_release_contract(self):
        projected = self.project()
        self.assertFalse(hasattr(projected, "to_dict"))
        self.assertFalse(projected.release_eligible)
        with self.assertRaises(FrozenInstanceError):
            projected.recommendations = ()
        with self.assertRaises(FrozenInstanceError):
            projected.recommendations[0].recommendation_action_text = "changed"
        self.assertEqual(self.project(), projected)

    def test_selection_missing_or_unsupported_fails_closed(self):
        with self.assertRaises(TypeError):
            project_local_v3_recommendations(self.gateway, self.admission)
        for selection in (None, False, "business-decision-package-v2",
                          "business-decision-package-v4"):
            with self.subTest(selection=selection):
                self.rejected(lambda: self.project(version=selection))

    def test_foreign_gateway_and_forged_assertions_fail_closed(self):
        foreign = VerifiedSnapshotGateway(
            trusted_issuer_id=fixtures.ISSUER, trusted_key_id=fixtures.KEY_ID,
            trusted_public_key=self.fixture.key.public_key(),
            expected_release_commit=fixtures.RELEASE,
        )
        self.rejected(lambda: self.project(gateway=foreign))
        self.rejected(lambda: self.project(gateway={"verified": True}))
        self.rejected(lambda: self.project(admission={"verified": True}))
        forged = LocalV3GovernedProjection(
            self.raw, self.admission.evidence, self.admission._sidecar_items,
        )
        self.rejected(lambda: self.project(admission=forged))

    def test_missing_forged_and_stale_evidence_fail_closed(self):
        self.rejected(lambda: self.project(admission=replace(
            self.admission, _sidecar_items=(),
        )))
        self.rejected(lambda: self.project(admission=replace(
            self.admission, evidence=replace(
                self.admission.evidence, snapshot_digest="0" * 64,
            ),
        )))
        for field, value in (("signature", "AAAA"),
                             ("snapshotDigest", "0" * 64),
                             ("producerReleaseCommit", "0" * 40)):
            with self.subTest(field=field):
                sidecar = dict(self.admission._sidecar_items)
                sidecar[field] = value
                self.rejected(lambda: self.project(admission=replace(
                    self.admission, _sidecar_items=tuple(sidecar.items()),
                )))
        with patch.object(self.gateway, "_expected_release_commit", "0" * 40):
            with self.assertRaises(VerifiedAdmissionError) as rejection:
                self.project()
        self.assertEqual(rejection.exception.code, "producer-version-mismatch")

    def test_cross_version_and_malformed_source_fail_closed(self):
        v2 = fixtures.produce_executive_assessment_snapshot(
            fixtures.request(50, "adequate", "none")
        )
        v2_raw = fixtures.encode(v2.serialized_snapshot)
        v2_sidecar = fixtures.ProducerSnapshotIssuer(
            self.fixture.key, issuer_id=fixtures.ISSUER,
            key_id=fixtures.KEY_ID, producer_release_commit=fixtures.RELEASE,
        ).issue(v2_raw)
        v2_admission = self.gateway.admit(v2_raw, v2_sidecar)
        self.rejected(lambda: self.project(admission=v2_admission))
        self.rejected(lambda: self.project(admission=replace(
            self.admission, _snapshot_bytes=b"{",
        )))
        self.rejected(lambda: project_local_v3_recommendations(
            self.gateway, None, package_contract_version=fixtures.V3,
        ))

    def test_changed_recommendation_content_never_falls_back_to_inference(self):
        def rows(snapshot):
            return snapshot["businessDecisionPackage"]["governedConclusions"][
                "recommendations"]

        edits = (
            lambda s: rows(s)[0].__setitem__("recommendationActionText", "changed"),
            lambda s: rows(s)[0].pop("recommendationActionText"),
            lambda s: rows(s).pop(),
            lambda s: rows(s).append(copy.deepcopy(rows(s)[0])),
            lambda s: rows(s).reverse(),
            lambda s: rows(s)[0].__setitem__("recommendationClassification", "monitor"),
            lambda s: rows(s)[0].__setitem__("findingId", "other-finding"),
            lambda s: rows(s)[0].__setitem__("recommendationDecisionIdentifier", "unknown"),
            lambda s: rows(s)[0].pop("recommendationDecisionIdentifier"),
            lambda s: s["businessDecisionPackage"]["versionMetadata"].__setitem__(
                "methodologyVersion", "other-methodology"),
        )
        for edit in edits:
            with self.subTest(edit=edit):
                self.rejected(lambda: self.project(self.altered_admission(edit)))

    def test_no_findings_link_cannot_be_invented(self):
        produced, raw = self.fixture.produced_v3(
            fixtures.request(50, "adequate", "none")
        )
        admission = self.gateway.admit_local_v3(
            raw, produced.attestation_sidecar,
            package_contract_version=fixtures.V3,
        )
        projected = self.project(admission)
        self.assertIsNone(projected.recommendations[0].finding_id)
        altered = copy.deepcopy(produced.serialized_snapshot)
        altered["businessDecisionPackage"]["governedConclusions"][
            "recommendations"][0]["findingId"] = "invented-finding"
        self.rejected(lambda: self.project(replace(
            admission, _snapshot_bytes=fixtures.encode(altered),
        )))


if __name__ == "__main__":
    unittest.main()
