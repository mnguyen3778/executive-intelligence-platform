"""Signed producer fixture through EIP's verified local delivery entry point."""

import base64
import copy
import json
import sys
import unittest
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


EIP_ROOT = Path(__file__).resolve().parents[2]
PRODUCER_ROOT = EIP_ROOT.parent / "nguyen-ai-assessment-service"
sys.path.insert(0, str(EIP_ROOT / "src"))
sys.path.insert(0, str(PRODUCER_ROOT / "src"))
sys.path.insert(0, str(PRODUCER_ROOT / "tests"))

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey  # noqa: E402
from assessment.executive_snapshot_handoff import produce_executive_assessment_snapshot  # noqa: E402
from assessment.executive_assessment_snapshot import (  # noqa: E402
    validate_executive_assessment_snapshot_serialization,
)
from assessment.producer_snapshot_attestation import (  # noqa: E402
    ProducerSnapshotIssuer, _signed_payload,
)
from test_golden_fixture_regression import request  # noqa: E402
from executive_intelligence_platform.executive_intelligence_package import (  # noqa: E402
    ExecutiveIntelligencePackageAssembler, ExecutiveIntelligencePackageRequest,
)
from executive_intelligence_platform.executive_intelligence_projection import (  # noqa: E402
    ExecutiveIntelligenceProjectionProjector, ExecutiveIntelligenceProjectionRequest,
)
from executive_intelligence_platform.projection_delivery.delivery import (  # noqa: E402
    WebsiteProjectionDeliveryContractPublisher, WebsiteProjectionDeliveryPublisher,
    WebsiteProjectionDeliveryRequest,
    _find_prohibited_key, _publish_governed_dashboard_content,
)
from executive_intelligence_platform.projection_delivery.verified_admission import (  # noqa: E402
    VerifiedAdmissionError, VerifiedSnapshotAdmission, VerifiedSnapshotGateway,
)
from executive_intelligence_platform.snapshot_catalog import SnapshotCatalog  # noqa: E402
from executive_intelligence_platform.snapshot_derivation import (  # noqa: E402
    SnapshotDerivationRequest, SnapshotDerivationRuntime,
)
from executive_intelligence_platform.snapshot_derivation.derivation import (  # noqa: E402
    GOVERNED_CONTENT_DERIVATION_RULE_VERSION,
)


RELEASE = "a075a679a053ee9d0eb9a32d7f0ffa2dc796f0da"
ISSUER = "nguyen-ai-assessment"
KEY_ID = "stage2-ephemeral-test"


def encode(snapshot):
    return json.dumps(snapshot, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def mutate(raw, edit):
    value = json.loads(raw)
    edit(value)
    return encode(value)


class VerifiedAdmissionTests(unittest.TestCase):
    def setUp(self):
        produced = produce_executive_assessment_snapshot(
            request(75, "mixed-strong", "two-high")
        )
        self.assertTrue(produced.is_success, produced.failure)
        self.snapshot = produced.serialized_snapshot
        self.raw = encode(self.snapshot)
        self.key = Ed25519PrivateKey.generate()
        self.issuer = ProducerSnapshotIssuer(
            self.key, issuer_id=ISSUER, key_id=KEY_ID,
            producer_release_commit=RELEASE,
        )
        self.sidecar = self.issuer.issue(self.raw)
        self.gateway = VerifiedSnapshotGateway(
            trusted_issuer_id=ISSUER, trusted_key_id=KEY_ID,
            trusted_public_key=self.key.public_key(),
            expected_release_commit=RELEASE,
        )

    def rejected(self, code, operation):
        with self.assertRaises(VerifiedAdmissionError) as context:
            operation()
        self.assertEqual(context.exception.code, code)

    def resign(self, sidecar):
        sidecar["signature"] = base64.b64encode(
            self.key.sign(_signed_payload(sidecar))
        ).decode("ascii")
        return sidecar

    def projection(self):
        entry = SnapshotCatalog().admit(
            self.snapshot,
            producer_snapshot_identity=self.sidecar["producerSnapshotIdentity"],
        ).entry
        derived = SnapshotDerivationRuntime().derive(
            entry, SnapshotDerivationRequest(GOVERNED_CONTENT_DERIVATION_RULE_VERSION)
        )
        packaged = ExecutiveIntelligencePackageAssembler().assemble(
            ExecutiveIntelligencePackageRequest(), derived.artifact,
        )
        projected = ExecutiveIntelligenceProjectionProjector().project(
            ExecutiveIntelligenceProjectionRequest(), packaged.package,
        )
        self.assertTrue(projected.projected, projected.issues)
        return projected.projection

    def test_governed_publisher_requires_gateway_admission(self):
        projection = self.projection()
        request = WebsiteProjectionDeliveryRequest()
        unsigned = _publish_governed_dashboard_content(request, projection)
        self.assertFalse(unsigned.delivered)
        self.assertEqual(tuple(issue.code for issue in unsigned.issues),
                         ("verified-admission-required",))
        admission = self.gateway.admit(self.raw, self.sidecar)
        signed = _publish_governed_dashboard_content(
            request, projection, verified_admission=admission,
            trusted_gateway=self.gateway,
        )
        self.assertTrue(signed.delivered, signed.issues)
        self.assertEqual(sum(len(group["items"]) for group in
                             signed.delivery.to_dict()["dashboardContent"].values()), 13)
        direct = WebsiteProjectionDeliveryPublisher().publish(
            replace(
                request, dashboard_content=signed.delivery.dashboard_content,
                field_classifications=request.field_classifications +
                (("dashboardContent", "restricted_assessment"),),
            ),
            projection,
        )
        self.assertFalse(direct.delivered)
        self.assertEqual(tuple(issue.code for issue in direct.issues),
                         ("verified-admission-required",))
        contract_publisher = WebsiteProjectionDeliveryContractPublisher()
        unsigned_publication = contract_publisher.publish(signed)
        self.assertFalse(unsigned_publication.published)
        self.assertEqual(tuple(issue.code for issue in unsigned_publication.issues),
                         ("verified-admission-required",))
        verified_publication = contract_publisher.publish(
            signed, verified_admission=admission, trusted_gateway=self.gateway,
        )
        self.assertTrue(verified_publication.published, verified_publication.issues)
        self.assertEqual(verified_publication.contract_instance.to_dict(),
                         signed.delivery.to_dict())

    def test_contract_publication_rejects_substituted_governed_delivery(self):
        admission = self.gateway.admit(self.raw, self.sidecar)
        original = self.gateway.deliver(admission).delivery
        changed = replace(
            original, delivery=replace(
                original.delivery,
                projection_reference=replace(
                    original.delivery.projection_reference,
                    producer_snapshot_identity="forged-snapshot",
                ),
            ),
        )
        result = WebsiteProjectionDeliveryContractPublisher().publish(
            changed, verified_admission=admission, trusted_gateway=self.gateway,
        )
        self.assertFalse(result.published)
        self.assertEqual(tuple(issue.code for issue in result.issues),
                         ("verified-admission-invalid",))

    def test_fabricated_admission_and_substituted_sidecar_rejected_by_publisher(self):
        projection = self.projection()
        admission = self.gateway.admit(self.raw, self.sidecar)
        fabricated = VerifiedSnapshotAdmission(
            self.raw, tuple(self.sidecar.items()), admission.evidence,
        )
        cases = (
            ("fabricated", fabricated),
            ("changed bytes", replace(admission, _snapshot_bytes=self.raw + b" ")),
            ("changed sidecar", replace(
                admission, _sidecar_items=tuple(dict(self.sidecar, signature="AAAA").items())
            )),
            ("changed evidence", replace(
                admission, evidence=replace(admission.evidence, key_id="other-key")
            )),
        )
        for name, candidate in cases:
            with self.subTest(name=name):
                result = _publish_governed_dashboard_content(
                    WebsiteProjectionDeliveryRequest(), projection,
                    verified_admission=candidate, trusted_gateway=self.gateway,
                )
                self.assertFalse(result.delivered)
                self.assertEqual(tuple(issue.code for issue in result.issues),
                                 ("verified-admission-invalid",))
        for options in ({"verified": True}, {"snapshot_digest": self.sidecar["snapshotDigest"]}):
            with self.subTest(options=tuple(options)):
                with self.assertRaises(TypeError):
                    _publish_governed_dashboard_content(
                        WebsiteProjectionDeliveryRequest(), projection, **options,
                    )

    def test_governed_publisher_rejects_every_conclusion_substitution(self):
        projection = self.projection()
        admission = self.gateway.admit(self.raw, self.sidecar)
        other = produce_executive_assessment_snapshot(request(75, "adequate", "critical"))
        self.assertTrue(other.is_success)
        valid_pair = other.serialized_snapshot["businessDecisionPackage"][
            "governedConclusions"]["assessmentRisk"]
        original = self.snapshot["businessDecisionPackage"][
            "governedConclusions"]["assessmentRisk"]
        self.assertNotEqual(valid_pair["riskClassification"],
                            original["riskClassification"])
        self.assertNotEqual(valid_pair["riskDecisionIdentifier"],
                            original["riskDecisionIdentifier"])
        changes = (
            ("risk classification", lambda g: g["assessmentRisk"].__setitem__(
                "riskClassification", valid_pair["riskClassification"])),
            ("risk decision ID", lambda g: g["assessmentRisk"].__setitem__(
                "riskDecisionIdentifier", valid_pair["riskDecisionIdentifier"])),
            ("both valid risk fields", lambda g: g.__setitem__(
                "assessmentRisk", valid_pair)),
            ("confidence", lambda g: g["confidence"].__setitem__(
                "confidenceClassification", "low-confidence")),
            ("recommendation", lambda g: g["recommendations"][0].__setitem__(
                "recommendationText", "forged recommendation")),
            ("summary", lambda g: g["executiveSummary"]["sectionText"].__setitem__(
                "risk-overview", "forged summary")),
        )
        source = projection.source_package.source_derived_artifact
        for name, change in changes:
            with self.subTest(name=name):
                conclusions = copy.deepcopy(source.to_dict()["governedConclusions"])
                change(conclusions)
                forged = replace(projection, source_package=replace(
                    projection.source_package,
                    source_derived_artifact=replace(
                        source, governed_conclusions=conclusions,
                    ),
                ))
                result = _publish_governed_dashboard_content(
                    WebsiteProjectionDeliveryRequest(), forged,
                    verified_admission=admission, trusted_gateway=self.gateway,
                )
                self.assertFalse(result.delivered)
                self.assertIsNone(result.delivery)

    def test_signed_fixture_admits_and_delivers_thirteen_items(self):
        before_raw = bytes(self.raw)
        before_sidecar = copy.deepcopy(self.sidecar)
        admission = self.gateway.admit(self.raw, self.sidecar)
        self.assertEqual(admission.evidence.snapshot_digest, self.sidecar["snapshotDigest"])
        self.assertEqual(admission.evidence.governed_conclusions_digest,
                         self.sidecar["governedConclusionsDigest"])
        self.assertEqual(admission.evidence.producer_snapshot_identity,
                         self.sidecar["producerSnapshotIdentity"])
        self.assertEqual(admission.evidence.issuer_id, ISSUER)
        self.assertEqual(admission.evidence.producer_release_commit, RELEASE)
        self.assertEqual(admission.evidence.key_id, KEY_ID)
        self.assertEqual(admission.evidence.verification_contract_version,
                         "producer-snapshot-attestation-v1")

        result = self.gateway.deliver(admission)
        self.assertTrue(result.delivery.delivered)
        self.assertEqual(result.evidence, admission.evidence)
        payload = result.delivery.delivery.to_dict()
        content = payload["dashboardContent"]
        self.assertEqual(tuple(content), (
            "summaries", "metrics", "findings", "risks", "recommendations"
        ))
        self.assertNotIn("decisions", content)
        self.assertEqual(tuple(len(section["items"]) for section in content.values()),
                         (7, 1, 2, 1, 2))
        self.assertEqual(sum(len(section["items"]) for section in content.values()), 13)
        governed = self.snapshot["businessDecisionPackage"]["governedConclusions"]
        self.assertEqual(
            [(item["fields"][0]["value"], item["summary"])
             for item in content["summaries"]["items"]],
            list(governed["executiveSummary"]["sectionText"].items()),
        )
        self.assertEqual(
            [item["fields"][0]["value"] for item in content["findings"]["items"]],
            [item["findingId"] for item in governed["severityAssignedFindings"]],
        )
        self.assertEqual(
            [item["fields"][0]["value"] for item in content["recommendations"]["items"]],
            [item["findingId"] for item in governed["recommendations"]],
        )
        self.assertEqual(content["risks"]["items"][0]["fields"][0]["value"],
                         governed["assessmentRisk"]["riskClassification"])
        self.assertEqual(content["metrics"]["items"][0]["fields"][0]["value"],
                         governed["confidence"]["confidenceClassification"])
        context = payload["versionContext"]
        self.assertEqual(context["businessDecisionPackageContractVersion"],
                         "business-decision-package-v2")
        self.assertEqual(context["assessmentVersion"],
                         "nguyen-ai-executive-assessment-v2")
        self.assertEqual(context["methodologyVersion"],
                         "business-decision-methodology-v1")
        self.assertEqual(context["derivationRuleVersion"],
                         "snapshot-derivation-governed-content-v2")
        self.assertEqual(payload["deliveryMetadata"]["deliveryContractVersion"],
                         "website-projection-delivery-contract-v1")
        self.assertEqual(payload["projectionReference"]["producerSnapshotIdentity"],
                         admission.evidence.producer_snapshot_identity)
        self.assertEqual(self.raw, before_raw)
        self.assertEqual(self.sidecar, before_sidecar)
        self.assertIsNone(_find_prohibited_key(payload))
        serialized = json.dumps(payload)
        for excluded in ("signature", "keyId", "snapshotDigest",
                         "governedConclusionsDigest", "businessDecisionPackage",
                         "sourcePackage", "sourceDerivedArtifact", "rawEvidence"):
            self.assertNotIn('"' + excluded + '":', serialized)

    def test_missing_sidecar_invalid_signature_and_untrusted_key(self):
        self.rejected("missing-attestation", lambda: self.gateway.admit(self.raw, None))
        signature = bytearray(base64.b64decode(self.sidecar["signature"]))
        signature[-1] ^= 1
        self.rejected("invalid-signature", lambda: self.gateway.admit(
            self.raw, dict(self.sidecar,
                           signature=base64.b64encode(signature).decode("ascii"))))
        other = VerifiedSnapshotGateway(
            trusted_issuer_id=ISSUER, trusted_key_id=KEY_ID,
            trusted_public_key=Ed25519PrivateKey.generate().public_key(),
            expected_release_commit=RELEASE,
        )
        self.rejected("invalid-signature", lambda: other.admit(self.raw, self.sidecar))
        other_key = self.resign(dict(self.sidecar, keyId="another-key"))
        self.rejected("unknown-key-id", lambda: self.gateway.admit(self.raw, other_key))

    def test_issuer_release_identity_and_contract_rejections(self):
        cases = (
            ("issuerId", "other-issuer", "unknown-issuer"),
            ("producerReleaseCommit", "0" * 40, "producer-version-mismatch"),
            ("producerSnapshotIdentity", "sha256:" + "0" * 64,
             "snapshot-identity-mismatch"),
            ("verificationContractVersion", "other-version",
             "unsupported-attestation-version"),
            ("packageContractVersion", "business-decision-package-v3",
             "producer-version-mismatch"),
        )
        for field, value, code in cases:
            with self.subTest(field=field):
                sidecar = self.resign(dict(self.sidecar, **{field: value}))
                self.rejected(code, lambda: self.gateway.admit(self.raw, sidecar))

    def test_altered_bytes_and_replayed_sidecar_rejected(self):
        altered = json.dumps(self.snapshot).encode("utf-8")
        self.assertEqual(json.loads(altered), json.loads(self.raw))
        self.rejected("snapshot-digest-mismatch",
                      lambda: self.gateway.admit(altered, self.sidecar))
        other = produce_executive_assessment_snapshot(request(50, "adequate", "medium"))
        self.assertTrue(other.is_success)
        self.rejected("snapshot-digest-mismatch", lambda: self.gateway.admit(
            encode(other.serialized_snapshot), self.sidecar))

    def test_all_five_governed_groups_are_bound(self):
        edits = (
            lambda g: g["severityAssignedFindings"][0].__setitem__("title", "changed"),
            lambda g: g["assessmentRisk"].__setitem__("riskClassification", "low-risk"),
            lambda g: g["confidence"].__setitem__("confidenceClassification", "low-confidence"),
            lambda g: g["recommendations"][0].__setitem__("recommendationClassification", "monitor"),
            lambda g: g["executiveSummary"]["sectionText"].__setitem__("risk-overview", "changed"),
        )
        for edit in edits:
            with self.subTest(edit=edit):
                altered = mutate(self.raw, lambda d: edit(d["businessDecisionPackage"][
                    "governedConclusions"]))
                self.rejected("snapshot-digest-mismatch",
                              lambda: self.gateway.admit(altered, self.sidecar))

    def test_valid_risk_pair_and_content_order_substitutions_rejected(self):
        other = produce_executive_assessment_snapshot(request(75, "adequate", "critical"))
        self.assertTrue(other.is_success)
        valid_pair = other.serialized_snapshot["businessDecisionPackage"][
            "governedConclusions"]["assessmentRisk"]
        original_pair = self.snapshot["businessDecisionPackage"][
            "governedConclusions"]["assessmentRisk"]
        self.assertNotEqual(valid_pair["riskClassification"],
                            original_pair["riskClassification"])
        self.assertNotEqual(valid_pair["riskDecisionIdentifier"],
                            original_pair["riskDecisionIdentifier"])
        substituted = mutate(self.raw, lambda d: d["businessDecisionPackage"][
            "governedConclusions"].__setitem__("assessmentRisk", valid_pair))
        self.assertTrue(validate_executive_assessment_snapshot_serialization(
            json.loads(substituted)).is_valid)
        edits = (
            lambda g: g.__setitem__("assessmentRisk", valid_pair),
            lambda g: g["severityAssignedFindings"].reverse(),
            lambda g: g["recommendations"].reverse(),
            lambda g: g["executiveSummary"]["sectionText"].__setitem__(
                "overall-assessment-overview",
                g["executiveSummary"]["sectionText"].pop("overall-assessment-overview")),
        )
        for edit in edits:
            with self.subTest(edit=edit):
                altered = mutate(self.raw, lambda d: edit(d["businessDecisionPackage"][
                    "governedConclusions"]))
                self.rejected("snapshot-digest-mismatch",
                              lambda: self.gateway.admit(altered, self.sidecar))

    def test_post_verification_snapshot_and_evidence_substitution_rejected(self):
        admission = self.gateway.admit(self.raw, self.sidecar)
        altered = mutate(self.raw, lambda d: d["businessDecisionPackage"][
            "governedConclusions"]["confidence"].__setitem__(
                "confidenceClassification", "low-confidence"))
        self.rejected("snapshot-digest-mismatch", lambda: self.gateway.deliver(
            replace(admission, _snapshot_bytes=altered)))
        self.rejected("verified-evidence-mismatch", lambda: self.gateway.deliver(
            replace(admission, evidence=replace(admission.evidence,
                                                issuer_id="other-issuer"))))
        self.rejected("unverified-derivation-input",
                      lambda: self.gateway.deliver(self.snapshot))
        copied_snapshot = admission.snapshot
        copied_snapshot["responseContractVersion"] = "tampered"
        self.assertEqual(self.gateway.deliver(admission).evidence, admission.evidence)

    def test_derived_package_replacement_cannot_cross_verified_path(self):
        admission = self.gateway.admit(self.raw, self.sidecar)
        assemble = ExecutiveIntelligencePackageAssembler.assemble

        def replace_package(assembler, request, artifact):
            original = assemble(assembler, request, artifact)
            forged = replace(original.package, source_derived_artifact=object())
            return replace(original, package=forged)

        with patch.object(ExecutiveIntelligencePackageAssembler, "assemble",
                          autospec=True, side_effect=replace_package):
            self.rejected("verified-chain-broken",
                          lambda: self.gateway.deliver(admission))

    def test_cryptographic_metadata_in_public_delivery_rejected(self):
        admission = self.gateway.admit(self.raw, self.sidecar)
        forged_payload = {
            "projectionReference": {
                "producerSnapshotIdentity": admission.evidence.producer_snapshot_identity,
            },
            "dashboardContent": {"signature": self.sidecar["signature"]},
        }
        forged = SimpleNamespace(delivered=True,
                                 delivery=SimpleNamespace(to_dict=lambda: forged_payload))
        with patch("executive_intelligence_platform.projection_delivery.verified_admission._publish_governed_dashboard_content",
                   return_value=forged):
            self.rejected("verified-chain-broken",
                          lambda: self.gateway.deliver(admission))
        self.assertEqual(_find_prohibited_key({"signature": "test"}), "$.signature")
        self.assertEqual(_find_prohibited_key({"summary": '{"keyId":"test"}'}),
                         "$.summary.keyId")

    def test_no_signer_or_trust_anchor_from_untrusted_inputs(self):
        self.rejected("unexpected-attestation-field", lambda: self.gateway.admit(
            self.raw, dict(self.sidecar, publicKey="attacker-key")))
        with self.assertRaises(TypeError):
            self.gateway.admit(self.raw, self.sidecar, trusted_public_key=self.key.public_key())
        self.rejected("invalid-snapshot-bytes", lambda: self.gateway.admit(
            self.snapshot, self.sidecar))


if __name__ == "__main__":
    unittest.main()
