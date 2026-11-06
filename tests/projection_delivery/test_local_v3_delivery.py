"""Explicit synthetic v3 delivery stays behind verified local admission."""

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
    WebsiteProjectionDeliveryContractPublisher,
)
from executive_intelligence_platform.projection_delivery.verified_admission import (  # noqa: E402
    LocalV3GovernedDelivery, LocalV3GovernedProjection,
    VerifiedAdmissionError, VerifiedSnapshotGateway, _local_v3_contract_valid,
)


class LocalV3DeliveryTests(unittest.TestCase):
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

    def deliver(self, admission=None, gateway=None, version=fixtures.V3):
        return (self.gateway if gateway is None else gateway).deliver_local_v3(
            self.admission if admission is None else admission,
            package_contract_version=version,
        )

    def rejected(self, action):
        with self.assertRaises(VerifiedAdmissionError):
            action()

    def test_explicit_delivery_reverifies_signed_snapshot(self):
        with patch.object(self.gateway, "admit_local_v3",
                          wraps=self.gateway.admit_local_v3) as reverify:
            result = self.deliver()
        self.assertIsInstance(result, LocalV3GovernedDelivery)
        self.assertEqual(reverify.call_count, 1)
        self.assertEqual(result.evidence, self.admission.evidence)
        self.assertEqual(result.governed_conclusions,
                         self.produced.serialized_snapshot["businessDecisionPackage"]
                         ["governedConclusions"])

    def test_eight_approved_actions_preserve_order_and_links(self):
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
                delivered = self.deliver(admission)
                source = produced.serialized_snapshot["businessDecisionPackage"]
                source_governed = source["governedConclusions"]
                governed = delivered.governed_conclusions
                self.assertEqual(governed, source_governed)
                self.assertEqual(governed["severityAssignedFindings"],
                                 source_governed["severityAssignedFindings"])
                findings = governed["severityAssignedFindings"]
                recommendations = governed["recommendations"]
                self.assertEqual(
                    [row["findingId"] for row in recommendations],
                    [row["findingId"] for row in findings] if findings else [None],
                )
                for row in recommendations:
                    self.assertEqual(tuple(row), fixtures.FIELDS_V2 +
                                     ("recommendationActionText",))
                    rule = row["recommendationDecisionIdentifier"]
                    self.assertEqual(row["recommendationActionText"],
                                     fixtures.APPROVED_RECOMMENDATION_ACTION_TEXT_BY_RULE[rule])
                    seen.add(rule)
        self.assertEqual(seen, set(fixtures.APPROVED_RECOMMENDATION_ACTION_TEXT_BY_RULE))

    def test_delivery_is_copy_based_and_does_not_mutate_admission(self):
        before = copy.deepcopy(self.admission.governed_conclusions)
        first = self.deliver()
        second = self.deliver()
        self.assertEqual(first, second)
        changed = first.governed_conclusions
        changed["recommendations"].clear()
        self.assertEqual(first.governed_conclusions, before)
        self.assertEqual(second.governed_conclusions, before)
        self.assertEqual(self.admission.governed_conclusions, before)
        with self.assertRaises(FrozenInstanceError):
            first.evidence = None

    def test_missing_or_unsupported_local_selection_rejected(self):
        with self.assertRaises(TypeError):
            self.gateway.deliver_local_v3(self.admission)
        for version in (None, False, "business-decision-package-v2",
                        "business-decision-package-v4"):
            with self.subTest(version=version):
                self.rejected(lambda: self.deliver(version=version))

    def test_forged_or_foreign_admission_rejected(self):
        forged = LocalV3GovernedProjection(
            self.raw, self.admission.evidence,
            self.admission._sidecar_items,
        )
        self.rejected(lambda: self.deliver(forged))
        foreign = VerifiedSnapshotGateway(
            trusted_issuer_id=fixtures.ISSUER, trusted_key_id=fixtures.KEY_ID,
            trusted_public_key=self.fixture.key.public_key(),
            expected_release_commit=fixtures.RELEASE,
        )
        self.rejected(lambda: self.deliver(gateway=foreign))
        self.rejected(lambda: self.deliver({"verified": True}))
        self.rejected(lambda: self.deliver(replace(
            self.admission, evidence=replace(self.admission.evidence,
                                             snapshot_digest="0" * 64))))

    def test_missing_or_altered_attestation_rejected_without_result(self):
        self.rejected(lambda: self.deliver(replace(self.admission,
                                                  _sidecar_items=())))
        with self.assertRaises(VerifiedAdmissionError) as malformed:
            self.deliver(replace(self.admission, _sidecar_items=(("invalid",),)))
        self.assertEqual(malformed.exception.code, "invalid-local-v3-evidence")
        for field, value in (("signature", "AAAA"),
                             ("snapshotDigest", "0" * 64),
                             ("issuerId", "other-issuer"),
                             ("producerReleaseCommit", "0" * 40)):
            with self.subTest(field=field):
                sidecar = dict(self.admission._sidecar_items)
                sidecar[field] = value
                self.rejected(lambda: self.deliver(replace(
                    self.admission, _sidecar_items=tuple(sidecar.items()))))

    def test_altered_content_and_recommendation_contract_rejected(self):
        self.rejected(lambda: self.deliver(replace(
            self.admission, _snapshot_bytes=self.raw + b" ")))
        for edit in (
            lambda row: row.pop("recommendationActionText"),
            lambda row: row.__setitem__("recommendationActionText", "changed"),
            lambda row: row.__setitem__("findingId", "other-finding"),
        ):
            with self.subTest(edit=edit):
                altered = copy.deepcopy(self.produced.serialized_snapshot)
                row = altered["businessDecisionPackage"]["governedConclusions"][
                    "recommendations"][0]
                edit(row)
                self.assertFalse(_local_v3_contract_valid(altered))
                self.rejected(lambda: self.deliver(replace(
                    self.admission, _snapshot_bytes=fixtures.encode(altered))))

    def test_wrong_trust_configuration_and_cross_version_rejected(self):
        for options in (
            {"trusted_issuer_id": "other-issuer",
             "trusted_public_key": self.fixture.key.public_key(),
             "expected_release_commit": fixtures.RELEASE},
            {"trusted_issuer_id": fixtures.ISSUER,
             "trusted_public_key": fixtures.Ed25519PrivateKey.generate().public_key(),
             "expected_release_commit": fixtures.RELEASE},
            {"trusted_issuer_id": fixtures.ISSUER,
             "trusted_public_key": self.fixture.key.public_key(),
             "expected_release_commit": "0" * 40},
        ):
            with self.subTest(options=tuple(options)):
                gateway = VerifiedSnapshotGateway(
                    trusted_key_id=fixtures.KEY_ID, **options,
                )
                self.rejected(lambda: gateway.admit_local_v3(
                    self.raw, self.produced.attestation_sidecar,
                    package_contract_version=fixtures.V3,
                ))
        v2 = fixtures.produce_executive_assessment_snapshot(
            fixtures.request(50, "adequate", "none")
        )
        v2_raw = fixtures.encode(v2.serialized_snapshot)
        v2_sidecar = fixtures.ProducerSnapshotIssuer(
            self.fixture.key, issuer_id=fixtures.ISSUER,
            key_id=fixtures.KEY_ID, producer_release_commit=fixtures.RELEASE,
        ).issue(v2_raw)
        self.rejected(lambda: self.gateway.admit_local_v3(
            v2_raw, v2_sidecar, package_contract_version=fixtures.V3,
        ))

    def test_production_authoritative_v3_and_v2_delivery_rejected(self):
        altered = copy.deepcopy(self.produced.serialized_snapshot)
        altered["responseStatus"]["productionAuthority"] = "PRODUCTION_AUTHORITATIVE"
        self.assertFalse(_local_v3_contract_valid(altered))
        self.rejected(lambda: self.deliver(replace(
            self.admission, _snapshot_bytes=fixtures.encode(altered))))
        self.rejected(lambda: self.gateway.deliver(self.admission))
        delivered = self.deliver()
        rejected_publication = WebsiteProjectionDeliveryContractPublisher().publish(
            delivered,
        )
        self.assertFalse(rejected_publication.published)
        self.assertIsNone(rejected_publication.contract_instance)

    def test_local_delivery_invokes_no_downstream_publisher(self):
        with patch.object(self.gateway, "deliver", side_effect=AssertionError(
                "v2 delivery invoked")) as v2_delivery, patch(
            "executive_intelligence_platform.projection_delivery.delivery."
            "WebsiteProjectionDeliveryContractPublisher.publish",
            side_effect=AssertionError("publication invoked"),
        ) as publisher:
            result = self.deliver()
        self.assertIsInstance(result, LocalV3GovernedDelivery)
        v2_delivery.assert_not_called()
        publisher.assert_not_called()


if __name__ == "__main__":
    unittest.main()
