"""Deterministic local fixture proof for synthetic v3 publication evidence."""

import sys
import unittest
from dataclasses import FrozenInstanceError, replace
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import test_local_v3_admission as fixtures  # noqa: E402
from executive_intelligence_platform.projection_delivery.delivery import (  # noqa: E402
    WebsiteProjectionDeliveryContractPublisher, WebsiteProjectionDeliveryPublisher,
)
from executive_intelligence_platform.projection_delivery.non_production_v3_publication_evidence import (  # noqa: E402
    APPROVED_FIELD_SCOPE, RECOMMENDATION_DECISION_TABLE_VERSION,
    SyntheticV3AuthoritySnapshot, SyntheticV3CurrentState,
    SyntheticV3PublicationRecord, SyntheticV3Selector,
    verify_synthetic_v3_publication,
)
from executive_intelligence_platform.projection_delivery.non_production_v3_serialized_artifact import (  # noqa: E402
    SERIALIZATION_PROFILE_VERSION, SyntheticV3ArtifactScope,
    create_synthetic_v3_artifact,
)
from executive_intelligence_platform.projection_delivery.recommendation_action_explain_delivery import (  # noqa: E402
    RECOMMENDATION_ACTION_EXPLAIN_DELIVERY_CONTRACT_VERSION as DELIVERY_V1,
    prepare_recommendation_action_explain_delivery,
)
from executive_intelligence_platform.projection_delivery.verified_admission import (  # noqa: E402
    VerifiedSnapshotGateway,
)


class SyntheticV3PublicationTests(unittest.TestCase):
    def setUp(self):
        fixture = fixtures.LocalV3AdmissionTests(
            methodName="test_selection_and_cross_version_evidence_fail_closed")
        fixture.setUp()
        self.gateway = fixture.gateway
        produced, raw = fixture.produced_v3(
            fixtures.request(75, "mixed-strong", "two-high"))
        self.admission = self.gateway.admit_local_v3(
            raw, produced.attestation_sidecar, package_contract_version=fixtures.V3)
        self.candidate = prepare_recommendation_action_explain_delivery(
            self.gateway, self.admission, package_contract_version=fixtures.V3,
            delivery_contract_version=DELIVERY_V1)
        projection = self.candidate.verified_projection
        self.scope = SyntheticV3ArtifactScope(
            "synthetic-business-entity", "synthetic-environment",
            "synthetic-engagement", True)
        self.artifact = create_synthetic_v3_artifact(
            self.candidate, self.gateway, self.admission,
            artifact_instance_id="synthetic-artifact-instance-A",
            trusted_scope=self.scope)
        self.record = SyntheticV3PublicationRecord(
            artifact_identity=self.artifact.artifact_instance_id,
            artifact_integrity_reference=self.artifact.integrity_reference,
            artifact_serialized_bytes=self.artifact.serialized_bytes,
            artifact_scope=self.scope,
            serialization_profile_version=SERIALIZATION_PROFILE_VERSION,
            occurrence="synthetic-occurrence-A", revision="synthetic-revision-1",
            series="synthetic-series-A",
            producer_snapshot_identity=projection.producer_snapshot_identity,
            verification_evidence=projection.verification_evidence,
            package_version=fixtures.V3,
            methodology_version=projection.methodology_version,
            decision_table_version=RECOMMENDATION_DECISION_TABLE_VERSION,
            field_scope=APPROVED_FIELD_SCOPE,
            delivery_contract_version=DELIVERY_V1)
        self.state = SyntheticV3CurrentState(self.record.occurrence,
                                             self.record.revision, "current")
        self.fixture = SyntheticV3AuthoritySnapshot(
            "synthetic-generation-1", True, (self.record,), (self.state,))
        self.selector = SyntheticV3Selector(self.record.artifact_identity,
                                            self.record.occurrence,
                                            self.record.revision,
                                            self.fixture.generation)

    def verify(self, *, selector=None, candidate=None, authority=None,
               trusted_fixture=None, gateway=None, admission=None,
               artifact=None, trusted_scope=None):
        return verify_synthetic_v3_publication(
            self.selector if selector is None else selector,
            self.candidate if candidate is None else candidate,
            self.fixture if authority is None else authority,
            trusted_fixture=self.fixture if trusted_fixture is None else trusted_fixture,
            gateway=self.gateway if gateway is None else gateway,
            admission=self.admission if admission is None else admission,
            artifact=self.artifact if artifact is None else artifact,
            trusted_scope=self.scope if trusted_scope is None else trusted_scope)

    def rejected(self, reason, **kwargs):
        result = self.verify(**kwargs)
        self.assertEqual((result.status, result.reason, result.evidence,
                          result.release_eligible),
                         ("SYNTHETIC_REJECTED", reason, None, False))
        self.assertNotIn("Take ", str(result))
        self.assertNotIn(fixtures.KEY_ID, str(result))

    def fixture_state(self, *records, states=None, generation=None, available=True):
        return SyntheticV3AuthoritySnapshot(
            generation or self.fixture.generation, available,
            records if records else (self.record,),
            states if states is not None else self.fixture.current_states)

    def under_fixture(self, authority, reason):
        self.rejected(reason, authority=authority, trusted_fixture=authority)

    def test_exact_signed_v3_match_and_non_release_result(self):
        result = self.verify()
        self.assertEqual((result.status, result.reason), ("SYNTHETIC_ACCEPTED", None))
        self.assertEqual(result.evidence.artifact_identity, self.record.artifact_identity)
        self.assertEqual(result.evidence.artifact_integrity_reference,
                         self.record.artifact_integrity_reference)
        self.assertEqual((result.evidence.occurrence, result.evidence.revision,
                          result.evidence.authority_generation),
                         (self.record.occurrence, self.record.revision,
                          self.fixture.generation))
        self.assertEqual(self.record.verification_evidence,
                         self.candidate.verified_projection.verification_evidence)
        self.assertEqual(self.record.delivery_contract_version, DELIVERY_V1)
        self.assertFalse(result.release_eligible)
        self.assertFalse(hasattr(result, "to_dict"))
        self.assertFalse(hasattr(result, "publish"))
        with self.assertRaises(FrozenInstanceError):
            result.release_eligible = True
        with self.assertRaises(FrozenInstanceError):
            result.evidence.revision = "changed"

    def test_distinct_occurrences_identical_artifact_bytes(self):
        other = replace(self.record, occurrence="synthetic-occurrence-B",
                        series="synthetic-series-B")
        state = replace(self.state, occurrence=other.occurrence)
        authority = self.fixture_state(self.record, other,
                                       states=(self.state, state))
        second = replace(self.selector, occurrence=other.occurrence)
        self.assertEqual(self.verify(authority=authority,
                                     trusted_fixture=authority).status,
                         "SYNTHETIC_ACCEPTED")
        result = self.verify(selector=second, authority=authority,
                             trusted_fixture=authority)
        self.assertEqual(result.status, "SYNTHETIC_ACCEPTED")
        self.assertEqual(result.evidence.artifact_integrity_reference,
                         self.record.artifact_integrity_reference)
        self.assertNotEqual(result.evidence.occurrence, self.record.occurrence)

    def test_identity_selection_and_generation_reject(self):
        for field, value, reason in (
            ("artifact_identity", "synthetic-other", "artifact-identity-mismatch"),
            ("occurrence", "synthetic-other", "publication-record-missing"),
            ("revision", "synthetic-other", "revision-identity-mismatch"),
            ("observed_generation", "synthetic-generation-0",
             "stale-publication-evidence"),
        ):
            with self.subTest(field=field):
                self.rejected(reason, selector=replace(self.selector, **{field: value}))
        self.rejected("malformed-evidence", selector=replace(self.selector,
                                                              occurrence=""))
        self.rejected("synthetic-fixture-mismatch",
                      authority=self.fixture_state(self.record,
                          generation="synthetic-generation-2"))

    def test_record_identity_versions_and_lineage_reject(self):
        for field, value, reason in (
            ("artifact_identity", "synthetic-other", "artifact-identity-mismatch"),
            ("artifact_integrity_reference", "sha256:" + "0" * 64,
             "artifact-integrity-mismatch"),
            ("artifact_serialized_bytes", b"forged-bytes",
             "artifact-integrity-mismatch"),
            ("artifact_scope", replace(self.scope, business_entity_id="other"),
             "artifact-scope-mismatch"),
            ("serialization_profile_version", "other-profile", "malformed-evidence"),
            ("producer_snapshot_identity", "other-snapshot",
             "producer-lineage-mismatch"),
            ("verification_evidence", replace(self.record.verification_evidence,
                snapshot_digest="0" * 64), "producer-lineage-mismatch"),
            ("package_version", "business-decision-package-v2",
             "v3-contract-mismatch"),
            ("methodology_version", "other-methodology", "v3-contract-mismatch"),
            ("decision_table_version", "other-decision-table", "v3-contract-mismatch"),
            ("delivery_contract_version", "website-projection-delivery-contract-v1",
             "v3-contract-mismatch"),
            ("field_scope", ("recommendationActionText", "secret"),
             "v3-contract-mismatch"),
        ):
            with self.subTest(field=field):
                record = replace(self.record, **{field: value})
                authority = self.fixture_state(record)
                self.under_fixture(authority, reason)

    def test_artifact_bytes_and_conflicting_instance_claims_reject(self):
        altered = replace(self.artifact, serialized_bytes=b"forged-bytes",
                          integrity_reference="sha256:" +
                          sha256(b"forged-bytes").hexdigest())
        self.rejected("artifact-integrity-mismatch", artifact=altered)
        self.rejected("artifact-evidence-missing", artifact=False)
        self.rejected("artifact-evidence-missing", trusted_scope=False)
        conflicting = replace(self.record, occurrence="synthetic-occurrence-B",
                              series="synthetic-series-B",
                              artifact_integrity_reference="sha256:" + "0" * 64)
        state = replace(self.state, occurrence=conflicting.occurrence)
        self.under_fixture(self.fixture_state(self.record, conflicting,
                           states=(self.state, state)),
                           "conflicting-artifact-instance-claims")
        alias = replace(self.record, artifact_identity=self.record.occurrence)
        selected = replace(self.selector, artifact_identity=alias.artifact_identity)
        authority = self.fixture_state(alias)
        self.rejected("artifact-identity-mismatch", selector=selected,
                      authority=authority, trusted_fixture=authority)

    def test_missing_conflicting_and_ambiguous_state_reject(self):
        self.under_fixture(self.fixture_state(states=()), "missing-current-state")
        other = replace(self.record, revision="synthetic-revision-2")
        self.under_fixture(self.fixture_state(self.record, other),
                           "conflicting-publication-records")
        self.under_fixture(self.fixture_state(self.record,
            states=(self.state, self.state)), "conflicting-current-state")
        other = replace(self.record, occurrence="synthetic-occurrence-B",
                        revision="synthetic-revision-2")
        state = replace(self.state, occurrence=other.occurrence,
                        revision=other.revision)
        self.under_fixture(self.fixture_state(self.record, other,
            states=(self.state, state)), "ambiguous-current-revision")

    def test_lifecycle_never_falls_back(self):
        for lifecycle in ("withdrawn", "revoked", "invalidated"):
            with self.subTest(lifecycle=lifecycle):
                authority = self.fixture_state(self.record,
                    states=(replace(self.state, state=lifecycle),))
                self.under_fixture(authority, "publication-" + lifecycle)
        newer = replace(self.record, occurrence="synthetic-occurrence-B",
                        revision="synthetic-revision-2")
        old_state = replace(self.state, state="superseded",
                            superseded_by=newer.occurrence)
        new_state = replace(self.state, occurrence=newer.occurrence,
                            revision=newer.revision)
        authority = self.fixture_state(self.record, newer,
                                       states=(old_state, new_state))
        self.under_fixture(authority, "publication-superseded")
        revoked = replace(new_state, state="revoked")
        authority = self.fixture_state(self.record, newer,
                                       states=(old_state, revoked))
        self.under_fixture(authority, "publication-superseded")
        self.rejected("publication-revoked",
            selector=replace(self.selector, occurrence=newer.occurrence,
                             revision=newer.revision),
            authority=authority, trusted_fixture=authority)

    def test_unavailable_malformed_and_forged_fixture_reject(self):
        self.rejected("publication-evidence-missing", authority=False)
        self.rejected("synthetic-fixture-missing", trusted_fixture=False)
        unavailable = replace(self.fixture, available=False)
        self.rejected("publication-evidence-unavailable", authority=unavailable)
        malformed = replace(self.fixture, records=(dict(unexpected="field"),))
        self.under_fixture(malformed, "malformed-evidence")
        forged = self.fixture_state(replace(self.record,
            artifact_integrity_reference="sha256:" + "0" * 64))
        self.rejected("synthetic-fixture-mismatch", authority=forged)
        self.under_fixture(SyntheticV3AuthoritySnapshot(
            self.fixture.generation, True, (), ()), "publication-record-missing")

    def test_invalid_candidate_and_same_gateway_reject(self):
        forged = replace(self.candidate, delivery_contract_version="other")
        self.rejected("invalid-v3-candidate", candidate=forged)
        object.__setattr__(forged, "release_eligible", True)
        self.rejected("invalid-v3-candidate", candidate=forged)
        foreign = VerifiedSnapshotGateway(
            trusted_issuer_id=fixtures.ISSUER, trusted_key_id=fixtures.KEY_ID,
            trusted_public_key=self.gateway._trusted_public_key,
            expected_release_commit=fixtures.RELEASE)
        self.rejected("invalid-v3-candidate", gateway=foreign)
        self.rejected("invalid-v3-candidate", admission=False)

    def test_no_v2_publisher_or_live_source(self):
        with patch.object(WebsiteProjectionDeliveryPublisher, "publish",
                          side_effect=AssertionError("v2 publisher called")) as v2, \
             patch.object(WebsiteProjectionDeliveryContractPublisher, "publish",
                          side_effect=AssertionError("v2 contract publisher called")) as contract:
            self.assertEqual(self.verify().status, "SYNTHETIC_ACCEPTED")
        v2.assert_not_called()
        contract.assert_not_called()
        self.assertFalse(hasattr(SyntheticV3AuthoritySnapshot, "connect"))


if __name__ == "__main__":
    unittest.main()
