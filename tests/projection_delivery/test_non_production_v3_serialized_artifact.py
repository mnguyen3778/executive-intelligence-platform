"""Bounded byte and identity proof for the synthetic v3 artifact profile."""

import json
import sys
import unittest
from dataclasses import FrozenInstanceError, replace
from hashlib import sha256
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import test_local_v3_admission as fixtures  # noqa: E402
from executive_intelligence_platform.projection_delivery.non_production_v3_serialized_artifact import (  # noqa: E402
    SERIALIZATION_PROFILE_VERSION, SyntheticV3ArtifactScope,
    create_synthetic_v3_artifact, verify_synthetic_v3_artifact,
)
from executive_intelligence_platform.projection_delivery.recommendation_action_explain_delivery import (  # noqa: E402
    RECOMMENDATION_ACTION_EXPLAIN_DELIVERY_CONTRACT_VERSION as DELIVERY_V1,
    prepare_recommendation_action_explain_delivery,
)
from executive_intelligence_platform.projection_delivery.verified_admission import (  # noqa: E402
    VerifiedAdmissionError, VerifiedSnapshotGateway,
)


def canonical(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


class SyntheticV3SerializedArtifactTests(unittest.TestCase):
    def setUp(self):
        fixture = fixtures.LocalV3AdmissionTests(
            methodName="test_selection_and_cross_version_evidence_fail_closed")
        fixture.setUp()
        self.producer_fixture = fixture
        self.gateway = fixture.gateway
        produced, raw = fixture.produced_v3(
            fixtures.request(75, "mixed-strong", "two-high"))
        self.admission = self.gateway.admit_local_v3(
            raw, produced.attestation_sidecar, package_contract_version=fixtures.V3)
        self.candidate = prepare_recommendation_action_explain_delivery(
            self.gateway, self.admission, package_contract_version=fixtures.V3,
            delivery_contract_version=DELIVERY_V1)
        self.scope = SyntheticV3ArtifactScope(
            "synthetic-business-entity", "synthetic-environment",
            "synthetic-engagement", True)
        self.instance_id = "synthetic-artifact-instance-A"
        self.artifact = self.build()

    def build(self, **changes):
        return create_synthetic_v3_artifact(
            changes.get("candidate", self.candidate),
            changes.get("gateway", self.gateway),
            changes.get("admission", self.admission),
            artifact_instance_id=changes.get("artifact_instance_id", self.instance_id),
            trusted_scope=changes.get("trusted_scope", self.scope))

    def verify(self, artifact=None, **changes):
        return verify_synthetic_v3_artifact(
            self.artifact if artifact is None else artifact,
            changes.get("candidate", self.candidate),
            changes.get("gateway", self.gateway),
            changes.get("admission", self.admission),
            expected_artifact_instance_id=changes.get("expected_id", self.instance_id),
            trusted_scope=changes.get("trusted_scope", self.scope))

    def rejected(self, artifact, **changes):
        result = self.verify(artifact, **changes)
        self.assertIs(result, False)
        self.assertNotIn("Take ", str(result))
        self.assertNotIn(fixtures.KEY_ID, str(result))

    def test_exact_bytes_digest_lineage_scope_and_content(self):
        self.assertTrue(self.verify())
        self.assertEqual(self.build(), self.artifact)
        self.assertFalse(self.artifact.release_eligible)
        self.assertEqual(self.artifact.integrity_reference,
                         "sha256:" + sha256(self.artifact.serialized_bytes).hexdigest())
        envelope = json.loads(self.artifact.serialized_bytes)
        self.assertEqual(self.artifact.serialized_bytes, canonical(envelope))
        self.assertEqual(tuple(envelope), tuple(sorted(envelope)))
        self.assertEqual(envelope["artifactInstanceId"], self.instance_id)
        self.assertEqual(envelope["artifactScope"], {
            "businessEntityId": self.scope.business_entity_id,
            "engagementId": self.scope.engagement_id,
            "environmentId": self.scope.environment_id})
        self.assertEqual(envelope["producerLineage"], {
            "producerSnapshotIdentity":
            self.candidate.verified_projection.verification_evidence.producer_snapshot_identity})
        self.assertEqual(envelope["serializationProfileVersion"],
                         SERIALIZATION_PROFILE_VERSION)
        self.assertEqual(envelope["deliveryContractVersion"], DELIVERY_V1)
        self.assertEqual(envelope["fieldScope"], ["recommendationActionText"])
        self.assertEqual(envelope["versionContext"], {
            "assessmentVersion": "nguyen-ai-executive-assessment-v2",
            "methodologyVersion": "business-decision-methodology-v1",
            "packageContractVersion": "business-decision-package-v3",
            "recommendationDecisionTableVersion":
            "recommendation-decision-table-set-v1",
            "snapshotResponseContractVersion": "executive-runtime-response-v1"})
        self.assertEqual(envelope["content"], self.candidate.content.to_dict())
        self.assertEqual([row["recommendationActionText"] for row in
                          envelope["content"]["recommendations"]],
                         [row.recommendation_action_text for row in
                          self.candidate.verified_projection.recommendations])
        self.assertEqual(tuple(envelope["content"]), ("recommendations",))
        self.assertTrue(all(tuple(row) == ("recommendationActionText",)
                            for row in envelope["content"]["recommendations"]))
        self.assertFalse(hasattr(self.artifact, "publish"))
        with self.assertRaises(FrozenInstanceError):
            self.artifact.artifact_instance_id = "changed"

    def test_distinct_instances_same_content_and_engagement_not_applicable(self):
        other = self.build(artifact_instance_id="synthetic-artifact-instance-B")
        self.assertNotEqual(other.serialized_bytes, self.artifact.serialized_bytes)
        self.assertEqual(json.loads(other.serialized_bytes)["content"],
                         json.loads(self.artifact.serialized_bytes)["content"])
        self.assertTrue(self.verify(other, expected_id="synthetic-artifact-instance-B"))
        no_engagement = SyntheticV3ArtifactScope(
            self.scope.business_entity_id, self.scope.environment_id, None, False)
        scoped = self.build(trusted_scope=no_engagement)
        self.assertTrue(self.verify(scoped, trusted_scope=no_engagement))
        self.assertIsNone(json.loads(scoped.serialized_bytes)["artifactScope"]["engagementId"])
        self.rejected(scoped)

    def test_bad_identity_or_scope_cannot_construct(self):
        bad_ids = (None, "", " space", "space ", "control\n", "é",
                   self.candidate.verified_projection.producer_snapshot_identity,
                   "synthetic-v3-artifact:" + "0" * 64,
                   "sha256:" + "0" * 64)
        for value in bad_ids:
            with self.subTest(identifier=value), self.assertRaises(VerifiedAdmissionError):
                self.build(artifact_instance_id=value)
        bad_scopes = (
            replace(self.scope, business_entity_id=""),
            replace(self.scope, environment_id="other "),
            replace(self.scope, engagement_id=None),
            replace(self.scope, engagement_applies=False),
            replace(self.scope, engagement_id="é"),
        )
        for value in bad_scopes:
            with self.subTest(scope=value), self.assertRaises(VerifiedAdmissionError):
                self.build(trusted_scope=value)

    def test_wrong_identity_digest_and_bytes_reject(self):
        self.rejected(self.artifact, expected_id="other-instance")
        for reference in ("sha512:" + "0" * 64, "sha256:" + "0" * 64,
                          "sha256:" + "A" * 64, "sha256:short"):
            with self.subTest(reference=reference):
                self.rejected(replace(self.artifact, integrity_reference=reference))
        self.rejected(replace(self.artifact, serialized_bytes=
                              self.artifact.serialized_bytes + b" "))
        self.rejected(replace(self.artifact, serialized_bytes=b"\xef\xbb\xbf" +
                              self.artifact.serialized_bytes))
        self.rejected(replace(self.artifact, serialized_bytes=b"\xff"))
        self.rejected(replace(self.artifact, artifact_instance_id="other-instance"))
        object.__setattr__(self.artifact, "release_eligible", True)
        self.rejected(self.artifact)

    def test_envelope_mutations_reject_even_with_recomputed_digest(self):
        source = json.loads(self.artifact.serialized_bytes)
        mutations = {
            "wrong-id": lambda x: x.update(artifactInstanceId="other-instance"),
            "missing-id": lambda x: x.pop("artifactInstanceId"),
            "wrong-contract": lambda x: x.update(deliveryContractVersion="v2"),
            "wrong-profile": lambda x: x.update(serializationProfileVersion="v2"),
            "wrong-lineage": lambda x: x["producerLineage"].update(
                producerSnapshotIdentity="other-snapshot"),
            "wrong-package": lambda x: x["versionContext"].update(
                packageContractVersion="business-decision-package-v2"),
            "wrong-methodology": lambda x: x["versionContext"].update(
                methodologyVersion="other"),
            "wrong-table": lambda x: x["versionContext"].update(
                recommendationDecisionTableVersion="other"),
            "wrong-be": lambda x: x["artifactScope"].update(businessEntityId="other"),
            "wrong-environment": lambda x: x["artifactScope"].update(
                environmentId="other"),
            "wrong-engagement": lambda x: x["artifactScope"].update(
                engagementId="other"),
            "unknown-envelope": lambda x: x.update(extra="secret"),
            "unknown-content": lambda x: x["content"].update(extra="secret"),
            "unknown-recommendation": lambda x: x["content"]["recommendations"][0].update(
                extra="secret"),
            "null-id": lambda x: x.update(artifactInstanceId=None),
            "null-text": lambda x: x["content"]["recommendations"][0].update(
                recommendationActionText=None),
            "numeric": lambda x: x.update(extra=1),
            "wrong-type": lambda x: x.update(fieldScope="recommendationActionText"),
            "changed-text": lambda x: x["content"]["recommendations"][0].update(
                recommendationActionText="changed"),
        }
        for name, mutate in mutations.items():
            with self.subTest(case=name):
                envelope = json.loads(self.artifact.serialized_bytes)
                mutate(envelope)
                data = canonical(envelope)
                forged = replace(self.artifact, serialized_bytes=data,
                                 integrity_reference="sha256:" + sha256(data).hexdigest())
                self.rejected(forged)

    def test_distinct_recommendation_order_rejects(self):
        canonical_input = replace(
            fixtures.request(75, "adequate", "critical"),
            findings=fixtures.request(75, "adequate", "critical").findings +
            fixtures.request(50, "adequate", "low").findings)
        produced, raw = self.producer_fixture.produced_v3(canonical_input)
        admission = self.gateway.admit_local_v3(
            raw, produced.attestation_sidecar, package_contract_version=fixtures.V3)
        candidate = prepare_recommendation_action_explain_delivery(
            self.gateway, admission, package_contract_version=fixtures.V3,
            delivery_contract_version=DELIVERY_V1)
        texts = [row.recommendation_action_text for row in
                 candidate.verified_projection.recommendations]
        self.assertGreaterEqual(len(set(texts)), 2)
        artifact = create_synthetic_v3_artifact(
            candidate, self.gateway, admission,
            artifact_instance_id=self.instance_id, trusted_scope=self.scope)
        envelope = json.loads(artifact.serialized_bytes)
        envelope["content"]["recommendations"].reverse()
        data = canonical(envelope)
        forged = replace(artifact, serialized_bytes=data,
                         integrity_reference="sha256:" + sha256(data).hexdigest())
        self.assertFalse(verify_synthetic_v3_artifact(
            forged, candidate, self.gateway, admission,
            expected_artifact_instance_id=self.instance_id,
            trusted_scope=self.scope))

    def test_noncanonical_duplicate_and_unicode_reject(self):
        data = self.artifact.serialized_bytes
        altered = (
            data.replace(b'"artifactInstanceId":',
                         b'"artifactInstanceId":"duplicate","artifactInstanceId":', 1),
            data.replace(b'"artifactInstanceId":', b' "artifactInstanceId":', 1),
            data.replace(b'"artifactInstanceId":', b'"artifactInstanceId" :', 1),
            data.replace(b'"artifactInstanceId":', b'"artifact\\u0049nstanceId":', 1),
            data.replace(b'"artifactInstanceId":', b'"artifactInstanceId":1,', 1),
            data.replace(b'"artifactInstanceId":', b'"artifactInstanceId":NaN,', 1),
            data.replace(b'"artifactInstanceId":', b'"artifactInstanceId":"\\ud800",', 1),
        )
        for changed in altered:
            with self.subTest(data=changed[:80]):
                forged = replace(self.artifact, serialized_bytes=changed,
                                 integrity_reference="sha256:" + sha256(changed).hexdigest())
                self.rejected(forged)

    def test_forged_candidate_or_gateway_reject(self):
        self.rejected(self.artifact, candidate=replace(
            self.candidate, delivery_contract_version="other"))
        foreign = VerifiedSnapshotGateway(
            trusted_issuer_id=fixtures.ISSUER, trusted_key_id=fixtures.KEY_ID,
            trusted_public_key=self.gateway._trusted_public_key,
            expected_release_commit=fixtures.RELEASE)
        self.rejected(self.artifact, gateway=foreign)
        self.rejected(self.artifact, admission=False)


if __name__ == "__main__":
    unittest.main()
