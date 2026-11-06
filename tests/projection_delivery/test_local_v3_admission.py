"""Explicit local v3 consumption of signed synthetic producer snapshots."""

import copy
import json
import sys
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch


EIP_ROOT = Path(__file__).resolve().parents[2]
PRODUCER_ROOT = EIP_ROOT.parent / "nguyen-ai-assessment-service"
sys.path.insert(0, str(EIP_ROOT / "src"))
sys.path.insert(0, str(PRODUCER_ROOT / "src"))
sys.path.insert(0, str(PRODUCER_ROOT / "tests"))

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey  # noqa: E402
from assessment.approved_methodology_runtime_config import (  # noqa: E402
    APPROVED_RECOMMENDATION_ACTION_TEXT_BY_RULE,
)
from assessment.business_decision_package import (  # noqa: E402
    ACTION_TEXT_BUSINESS_DECISION_PACKAGE_CONTRACT_VERSION,
)
from assessment.executive_snapshot_handoff import produce_executive_assessment_snapshot  # noqa: E402
from assessment.governed_assessment_input import FindingInput  # noqa: E402
from assessment.producer_snapshot_attestation import (  # noqa: E402
    ProducerSnapshotIssuer, ProducerSnapshotVerifier,
    V3_VERIFICATION_CONTRACT_VERSION,
)
from test_golden_fixture_regression import request  # noqa: E402
from executive_intelligence_platform.projection_delivery.verified_admission import (  # noqa: E402
    LocalV3GovernedProjection, VerifiedAdmissionError, VerifiedSnapshotGateway,
    _local_v3_contract_valid,
)


RELEASE = "a075a679a053ee9d0eb9a32d7f0ffa2dc796f0da"
ISSUER = "nguyen-ai-assessment"
KEY_ID = "local-v3-eip-test"
V3 = ACTION_TEXT_BUSINESS_DECISION_PACKAGE_CONTRACT_VERSION
FIELDS_V2 = (
    "findingId", "recommendationClassification",
    "recommendationDecisionIdentifier", "recommendationDecisionTableVersion",
)


def encode(snapshot):
    return json.dumps(snapshot, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


class LocalV3AdmissionTests(unittest.TestCase):
    def setUp(self):
        self.key = Ed25519PrivateKey.generate()
        self.issuer = ProducerSnapshotIssuer(
            self.key, issuer_id=ISSUER, key_id=KEY_ID,
            producer_release_commit=RELEASE,
            verification_contract_version=V3_VERIFICATION_CONTRACT_VERSION,
        )
        self.producer_verifier = ProducerSnapshotVerifier(
            trusted_issuer_id=ISSUER, trusted_keys={KEY_ID: self.key.public_key()},
            expected_release_commit=RELEASE,
            verification_contract_version=V3_VERIFICATION_CONTRACT_VERSION,
        )
        self.gateway = VerifiedSnapshotGateway(
            trusted_issuer_id=ISSUER, trusted_key_id=KEY_ID,
            trusted_public_key=self.key.public_key(), expected_release_commit=RELEASE,
        )

    def produced_v3(self, canonical):
        result = produce_executive_assessment_snapshot(
            canonical, local_package_contract_version=V3,
            local_v3_issuer=self.issuer, local_v3_verifier=self.producer_verifier,
        )
        self.assertTrue(result.is_success, result.failure)
        return result, encode(result.serialized_snapshot)

    def rejected(self, operation):
        with self.assertRaises(VerifiedAdmissionError):
            operation()

    def test_default_v2_and_explicit_local_v3_preserve_all_eight_decisions(self):
        cases = [
            request(75, "adequate", "critical"),
            request(75, "mixed-strong", "two-high"),
            request(50, "adequate", "medium"),
            request(50, "adequate", "low"),
            request(100, "strong", "strength"),
            request(50, "adequate", "none"),
        ]
        for kind, basis in (("Observation", "observation"),
                            ("Opportunity", "opportunity")):
            finding = FindingInput(
                "finding-local-" + kind.lower(), "Local finding", "POC", (),
                "fixture-input", kind, basis, ("fixture-input",),
            )
            cases.append(replace(request(50, "adequate", "none"), findings=(finding,)))

        seen = set()
        for canonical in cases:
            with self.subTest(findings=canonical.findings):
                v2 = produce_executive_assessment_snapshot(canonical)
                self.assertTrue(v2.is_success, v2.failure)
                v2_raw = encode(v2.serialized_snapshot)
                v2_issuer = ProducerSnapshotIssuer(
                    self.key, issuer_id=ISSUER, key_id=KEY_ID,
                    producer_release_commit=RELEASE,
                )
                v2_admitted = self.gateway.admit(v2_raw, v2_issuer.issue(v2_raw))
                self.assertEqual(v2_admitted.snapshot, v2.serialized_snapshot)

                v3, raw = self.produced_v3(canonical)
                self.rejected(lambda: self.gateway.admit(raw, v3.attestation_sidecar))
                projected = self.gateway.admit_local_v3(
                    raw, v3.attestation_sidecar, package_contract_version=V3,
                )
                self.assertIsInstance(projected, LocalV3GovernedProjection)
                self.assertEqual(projected.evidence.verification_contract_version,
                                 V3_VERIFICATION_CONTRACT_VERSION)
                self.assertEqual(projected.governed_conclusions,
                                 v3.serialized_snapshot["businessDecisionPackage"]["governedConclusions"])
                old = v2.serialized_snapshot["businessDecisionPackage"]
                new = copy.deepcopy(v3.serialized_snapshot["businessDecisionPackage"])
                new["versionMetadata"]["contractVersion"] = "business-decision-package-v2"
                for row in new["governedConclusions"]["recommendations"]:
                    self.assertEqual(tuple(row), FIELDS_V2 + ("recommendationActionText",))
                    rule = row["recommendationDecisionIdentifier"]
                    self.assertEqual(row["recommendationActionText"],
                                     APPROVED_RECOMMENDATION_ACTION_TEXT_BY_RULE[rule])
                    seen.add(rule)
                    del row["recommendationActionText"]
                self.assertEqual(new, old)
                self.assertTrue(all(tuple(row) == FIELDS_V2 for row in
                                    old["governedConclusions"]["recommendations"]))
                if not canonical.findings:
                    self.assertIsNone(new["governedConclusions"]["recommendations"][0]["findingId"])
                changed_copy = projected.governed_conclusions
                changed_copy["recommendations"].clear()
                self.assertEqual(projected.governed_conclusions,
                                 v3.serialized_snapshot["businessDecisionPackage"]["governedConclusions"])
                self.rejected(lambda: self.gateway.deliver(projected))
        self.assertEqual(seen, set(APPROVED_RECOMMENDATION_ACTION_TEXT_BY_RULE))

    def test_selection_and_cross_version_evidence_fail_closed(self):
        v3, raw = self.produced_v3(request(50, "adequate", "none"))
        for selected in (None, False, 3, "business-decision-package-v2",
                         "business-decision-package-v4"):
            with self.subTest(selected=selected):
                self.rejected(lambda: self.gateway.admit_local_v3(
                    raw, v3.attestation_sidecar, package_contract_version=selected,
                ))
        with self.assertRaises(TypeError):
            self.gateway.admit_local_v3(raw, v3.attestation_sidecar)
        v2 = produce_executive_assessment_snapshot(request(50, "adequate", "none"))
        v2_raw = encode(v2.serialized_snapshot)
        v2_issuer = ProducerSnapshotIssuer(
            self.key, issuer_id=ISSUER, key_id=KEY_ID,
            producer_release_commit=RELEASE,
        )
        self.rejected(lambda: self.gateway.admit_local_v3(
            v2_raw, v2_issuer.issue(v2_raw), package_contract_version=V3,
        ))
        self.rejected(lambda: self.gateway.admit_local_v3(
            raw, None, package_contract_version=V3,
        ))

    def test_incorrect_expected_producer_release_rejects_local_v3(self):
        v3, raw = self.produced_v3(request(50, "adequate", "none"))
        wrong_release_gateway = VerifiedSnapshotGateway(
            trusted_issuer_id=ISSUER, trusted_key_id=KEY_ID,
            trusted_public_key=self.key.public_key(),
            expected_release_commit="0" * 40,
        )
        projection = None
        with patch.object(wrong_release_gateway, "deliver") as downstream_delivery:
            with self.assertRaises(VerifiedAdmissionError) as rejection:
                projection = wrong_release_gateway.admit_local_v3(
                    raw, v3.attestation_sidecar, package_contract_version=V3,
                )
            self.assertEqual(rejection.exception.code, "producer-version-mismatch")
            self.assertIsNone(projection)
            downstream_delivery.assert_not_called()

    def test_untrusted_issuer_key_and_tampering_are_rejected(self):
        v3, raw = self.produced_v3(request(75, "mixed-strong", "two-high"))
        wrong_issuer = VerifiedSnapshotGateway(
            trusted_issuer_id="other-issuer", trusted_key_id=KEY_ID,
            trusted_public_key=self.key.public_key(), expected_release_commit=RELEASE,
        )
        self.rejected(lambda: wrong_issuer.admit_local_v3(
            raw, v3.attestation_sidecar, package_contract_version=V3,
        ))
        wrong_key = VerifiedSnapshotGateway(
            trusted_issuer_id=ISSUER, trusted_key_id=KEY_ID,
            trusted_public_key=Ed25519PrivateKey.generate().public_key(),
            expected_release_commit=RELEASE,
        )
        self.rejected(lambda: wrong_key.admit_local_v3(
            raw, v3.attestation_sidecar, package_contract_version=V3,
        ))
        for field, bad_value in (("snapshotDigest", "0" * 64),
                                 ("signature", "AAAA"),
                                 ("verificationContractVersion", "producer-snapshot-attestation-v1")):
            sidecar = dict(v3.attestation_sidecar)
            sidecar[field] = bad_value
            self.rejected(lambda: self.gateway.admit_local_v3(
                raw, sidecar, package_contract_version=V3,
            ))
        for edit in (
            lambda s: s["businessDecisionPackage"]["governedConclusions"]["recommendations"][0].update({"recommendationActionText": "changed"}),
            lambda s: s["businessDecisionPackage"]["governedConclusions"]["recommendations"][0].update({"findingId": "changed"}),
            lambda s: s["businessDecisionPackage"]["governedConclusions"]["recommendations"].reverse(),
            lambda s: s["businessDecisionPackage"]["versionMetadata"].update({"contractVersion": "business-decision-package-v2"}),
            lambda s: s["responseStatus"].update({"productionAuthority": "PRODUCTION_AUTHORITATIVE"}),
        ):
            altered = copy.deepcopy(v3.serialized_snapshot)
            edit(altered)
            self.rejected(lambda: self.gateway.admit_local_v3(
                encode(altered), v3.attestation_sidecar, package_contract_version=V3,
            ))

    def test_local_contract_check_rejects_production_and_wrong_text(self):
        v3, _raw = self.produced_v3(request(50, "adequate", "medium"))
        invalid = copy.deepcopy(v3.serialized_snapshot)
        invalid["responseStatus"]["productionAuthority"] = "PRODUCTION_AUTHORITATIVE"
        self.assertFalse(_local_v3_contract_valid(invalid))
        invalid = copy.deepcopy(v3.serialized_snapshot)
        invalid["businessDecisionPackage"]["governedConclusions"]["recommendations"][0]["recommendationActionText"] = "changed"
        self.assertFalse(_local_v3_contract_valid(invalid))


if __name__ == "__main__":
    unittest.main()
