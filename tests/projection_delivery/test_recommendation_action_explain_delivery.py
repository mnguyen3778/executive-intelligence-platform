"""Local-only tests for the non-releasable v3 action delivery boundary."""

import copy
import sys
import unittest
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
from unittest.mock import patch


EIP_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(EIP_ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import test_local_v3_admission as fixtures  # noqa: E402
from executive_intelligence_platform.projection_delivery.delivery import (  # noqa: E402
    WebsiteProjectionDeliveryContractPublisher, WebsiteProjectionDeliveryPublisher,
)
from executive_intelligence_platform.projection_delivery.recommendation_action_explain_delivery import (  # noqa: E402
    RECOMMENDATION_ACTION_EXPLAIN_DELIVERY_CONTRACT_VERSION as DELIVERY_V1,
    InternalRecommendationActionExplainDeliveryCandidate,
    RecommendationActionContentItem,
    RecommendationActionContentProjection,
    prepare_recommendation_action_explain_delivery,
)
from executive_intelligence_platform.projection_delivery.verified_admission import (  # noqa: E402
    VerifiedAdmissionError, VerifiedSnapshotGateway,
)
from executive_intelligence_platform.snapshot_derivation.local_v3_recommendation_projection import (  # noqa: E402
    project_local_v3_recommendations,
)


class RecommendationActionExplainDeliveryTests(unittest.TestCase):
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

    def prepare(self, *, gateway=None, admission=None, package_version=fixtures.V3,
                delivery_version=DELIVERY_V1):
        return prepare_recommendation_action_explain_delivery(
            self.gateway if gateway is None else gateway,
            self.admission if admission is None else admission,
            package_contract_version=package_version,
            delivery_contract_version=delivery_version,
        )

    def altered_admission(self, edit):
        snapshot = copy.deepcopy(self.produced.serialized_snapshot)
        edit(snapshot)
        return replace(self.admission, _snapshot_bytes=fixtures.encode(snapshot))

    def assert_rejected(self, operation):
        with self.assertRaises(VerifiedAdmissionError) as raised:
            operation()
        self.assertNotIn("Take ", str(raised.exception))
        self.assertNotIn("sha256:", str(raised.exception))
        self.assertNotIn(fixtures.KEY_ID, str(raised.exception))

    def test_signed_v3_content_preserves_versions_order_and_exact_text(self):
        candidate = self.prepare()
        source = self.produced.serialized_snapshot["businessDecisionPackage"]
        records = source["governedConclusions"]["recommendations"]
        self.assertIsInstance(candidate, InternalRecommendationActionExplainDeliveryCandidate)
        self.assertEqual(candidate.delivery_contract_version, DELIVERY_V1)
        self.assertEqual(candidate.verified_projection.package_contract_version, fixtures.V3)
        self.assertEqual(candidate.verified_projection.methodology_version,
                         source["versionMetadata"]["methodologyVersion"])
        self.assertEqual(candidate.verified_projection.verification_evidence,
                         self.admission.evidence)
        self.assertEqual(candidate.verified_projection.producer_snapshot_identity,
                         self.admission.evidence.producer_snapshot_identity)
        self.assertEqual(candidate.content.to_dict(), {
            "recommendations": [
                {"recommendationActionText": record["recommendationActionText"]}
                for record in records
            ],
        })
        self.assertEqual(tuple(item.finding_id for item in
                               candidate.verified_projection.recommendations),
                         tuple(record["findingId"] for record in records))
        self.assertFalse(candidate.verified_projection.release_eligible)
        self.assertFalse(candidate.release_eligible)

    def test_no_findings_has_one_null_link_and_exact_content(self):
        produced, raw = self.fixture.produced_v3(
            fixtures.request(50, "adequate", "none")
        )
        admission = self.gateway.admit_local_v3(
            raw, produced.attestation_sidecar, package_contract_version=fixtures.V3,
        )
        candidate = self.prepare(admission=admission)
        self.assertEqual(len(candidate.verified_projection.recommendations), 1)
        self.assertIsNone(candidate.verified_projection.recommendations[0].finding_id)
        self.assertEqual(candidate.content.to_dict(), {
            "recommendations": [{"recommendationActionText":
                produced.serialized_snapshot["businessDecisionPackage"]
                ["governedConclusions"]["recommendations"][0]
                ["recommendationActionText"]}],
        })

    def test_same_gateway_and_signed_reverification_required(self):
        foreign = VerifiedSnapshotGateway(
            trusted_issuer_id=fixtures.ISSUER, trusted_key_id=fixtures.KEY_ID,
            trusted_public_key=self.fixture.key.public_key(),
            expected_release_commit=fixtures.RELEASE,
        )
        self.assert_rejected(lambda: prepare_recommendation_action_explain_delivery(
            self.gateway, None, package_contract_version=fixtures.V3,
            delivery_contract_version=DELIVERY_V1))
        self.assert_rejected(lambda: self.prepare(gateway=foreign))
        self.assert_rejected(lambda: self.prepare(gateway={"verified": True}))
        self.assert_rejected(lambda: self.prepare(admission={"verified": True}))
        sidecar = dict(self.admission._sidecar_items)
        sidecar["signature"] = "AAAA"
        self.assert_rejected(lambda: self.prepare(admission=replace(
            self.admission, _sidecar_items=tuple(sidecar.items()))))
        self.assert_rejected(lambda: self.prepare(admission=replace(
            self.admission, _snapshot_bytes=self.raw + b" ")))

    def test_versions_are_exact_and_never_downgrade(self):
        for version in (None, "", "website-projection-delivery-contract-v1",
                        "website-recommendation-action-explain-delivery-contract-v2"):
            with self.subTest(delivery_version=version):
                self.assert_rejected(lambda: self.prepare(delivery_version=version))
        for version in (None, "", "business-decision-package-v2",
                        "business-decision-package-v4"):
            with self.subTest(package_version=version):
                self.assert_rejected(lambda: self.prepare(package_version=version))
        self.assert_rejected(lambda: self.prepare(admission=self.altered_admission(
            lambda s: s["businessDecisionPackage"]["versionMetadata"].__setitem__(
                "methodologyVersion", "other-methodology"))))

    def test_changed_records_and_unknown_fields_fail_closed(self):
        def rows(snapshot):
            return snapshot["businessDecisionPackage"]["governedConclusions"][
                "recommendations"]

        edits = (
            lambda s: rows(s)[0].__setitem__("recommendationActionText", "changed"),
            lambda s: rows(s).reverse(),
            lambda s: rows(s)[0].__setitem__("findingId", "wrong-finding"),
            lambda s: rows(s).append(copy.deepcopy(rows(s)[0])),
            lambda s: rows(s).pop(),
            lambda s: rows(s)[0].__setitem__("unexpected", "value"),
            lambda s: rows(s)[0].pop("recommendationActionText"),
        )
        for edit in edits:
            with self.subTest(edit=edit):
                self.assert_rejected(lambda: self.prepare(
                    admission=self.altered_admission(edit)))

    def test_invalid_no_findings_semantics_fail_closed(self):
        produced, raw = self.fixture.produced_v3(
            fixtures.request(50, "adequate", "none")
        )
        admission = self.gateway.admit_local_v3(
            raw, produced.attestation_sidecar, package_contract_version=fixtures.V3,
        )
        snapshot = copy.deepcopy(produced.serialized_snapshot)
        snapshot["businessDecisionPackage"]["governedConclusions"][
            "recommendations"][0]["findingId"] = "invented"
        self.assert_rejected(lambda: self.prepare(admission=replace(
            admission, _snapshot_bytes=fixtures.encode(snapshot))))

    def test_candidate_and_content_are_frozen_and_minimized(self):
        candidate = self.prepare()
        with self.assertRaises(FrozenInstanceError):
            candidate.release_eligible = True
        with self.assertRaises(FrozenInstanceError):
            candidate.content.recommendations = ()
        with self.assertRaises(FrozenInstanceError):
            candidate.content.recommendations[0].recommendation_action_text = "changed"
        with self.assertRaises(TypeError):
            RecommendationActionContentItem("text", finding_id="secret")
        with self.assertRaises(TypeError):
            RecommendationActionContentProjection((), verification_evidence="secret")
        payload = candidate.content.to_dict()
        self.assertEqual(tuple(payload), ("recommendations",))
        self.assertTrue(all(tuple(row) == ("recommendationActionText",)
                            for row in payload["recommendations"]))
        self.assertNotIn(candidate.verified_projection.producer_snapshot_identity,
                         str(payload))
        self.assertFalse(hasattr(candidate, "to_dict"))
        self.assertFalse(hasattr(candidate, "serialize"))
        self.assertFalse(hasattr(candidate, "publish"))
        self.assertFalse(hasattr(candidate, "release"))

    def test_unexpected_release_eligibility_or_content_field_is_rejected(self):
        valid = project_local_v3_recommendations(
            self.gateway, self.admission, package_contract_version=fixtures.V3)
        object.__setattr__(valid, "release_eligible", True)
        with patch(
            "executive_intelligence_platform.projection_delivery."
            "recommendation_action_explain_delivery.project_local_v3_recommendations",
            return_value=valid,
        ):
            self.assert_rejected(self.prepare)
        with patch.object(RecommendationActionContentProjection, "to_dict",
                          return_value={"recommendations": [], "findingId": "secret"}):
            self.assert_rejected(self.prepare)

    def test_internal_path_calls_no_publisher_or_authority(self):
        with patch.object(self.gateway, "deliver_local_v3",
                          wraps=self.gateway.deliver_local_v3) as deliver, patch.object(
            WebsiteProjectionDeliveryPublisher, "publish",
            side_effect=AssertionError("v2 publisher called"),
        ) as v2, patch.object(
            WebsiteProjectionDeliveryContractPublisher, "publish",
            side_effect=AssertionError("v2 contract publisher called"),
        ) as contract, patch(
            "executive_intelligence_platform.projection_delivery."
            "non_production_publication_revision_evidence.verify_publication",
            side_effect=AssertionError("publication authority called"),
        ) as publication:
            candidate = self.prepare()
        deliver.assert_called_once_with(
            self.admission, package_contract_version=fixtures.V3)
        v2.assert_not_called()
        contract.assert_not_called()
        publication.assert_not_called()
        self.assertFalse(candidate.release_eligible)


if __name__ == "__main__":
    unittest.main()
