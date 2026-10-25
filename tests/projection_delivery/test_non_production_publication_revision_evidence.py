"""Synthetic-only publication evidence tests; no production lifecycle source."""

import sys
import unittest
from dataclasses import FrozenInstanceError, replace
from hashlib import sha256
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import test_verified_admission as existing_fixtures  # noqa: E402
from executive_intelligence_platform.projection_delivery.delivery import (  # noqa: E402
    WebsiteProjectionDeliveryContractInstance,
)
from executive_intelligence_platform.projection_delivery.non_production_publication_revision_evidence import (  # noqa: E402
    PublicationSelector,
    SyntheticAuthoritySnapshot,
    SyntheticPublicationRecord,
    verify_publication,
)


class PublicationRevisionEvidenceTests(unittest.TestCase):
    def setUp(self):
        fixture = existing_fixtures.VerifiedAdmissionTests(
            methodName="test_governed_publisher_requires_gateway_admission"
        )
        fixture.setUp()
        self.gateway = fixture.gateway
        self.admission = fixture.gateway.admit(fixture.raw, fixture.sidecar)
        verified = self.gateway.deliver(self.admission)
        self.raw = WebsiteProjectionDeliveryContractInstance(
            verified.delivery.delivery
        ).serialize().encode("utf-8")
        self.record = SyntheticPublicationRecord(
            occurrence="synthetic-occurrence-A", revision="synthetic-revision-A",
            series="synthetic-series-A", artifact_bytes=self.raw,
            content_sha256=sha256(self.raw).hexdigest(),
            contract_version=verified.delivery.delivery.delivery_metadata.delivery_contract_version,
            policy_version=verified.delivery.delivery.delivery_metadata.publication_policy_version,
            producer_snapshot_identity=verified.evidence.producer_snapshot_identity,
            verification_evidence=verified.evidence, state="current", eligible=True,
        )
        self.authority = SyntheticAuthoritySnapshot("synthetic-generation-1", True,
                                                    (self.record,))
        self.selector = PublicationSelector(self.record.occurrence, self.record.revision,
                                            self.authority.generation)

    def verify(self, selector=None, raw=None, authority=None, admission=None):
        return verify_publication(
            self.selector if selector is None else selector,
            self.raw if raw is None else raw,
            self.authority if authority is None else authority,
            admission=self.admission if admission is None else admission,
            gateway=self.gateway,
        )

    def rejected(self, reason, **changes):
        result = self.verify(**changes)
        self.assertEqual((result.status, result.reason, result.evidence),
                         ("NOT_ACCEPTED", reason, None))

    def state(self, *records, generation="synthetic-generation-1", available=True):
        return SyntheticAuthoritySnapshot(generation, available, records)

    def test_first_publication(self):
        result = self.verify()
        self.assertEqual((result.status, result.reason), ("ACCEPTED", None))
        self.assertEqual(result.evidence.occurrence, self.record.occurrence)
        self.assertEqual(result.evidence.revision, self.record.revision)
        self.assertEqual(result, self.verify())
        self.assertFalse(hasattr(result.evidence, "artifact_bytes"))
        self.assertFalse(hasattr(result.evidence, "resource"))
        self.assertFalse(hasattr(result.evidence, "principal"))
        with self.assertRaises(FrozenInstanceError):
            result.evidence.revision = "changed"

    def test_valid_new_current_revision(self):
        newer = replace(self.record, occurrence="synthetic-occurrence-B",
                        revision="synthetic-revision-B")
        old = replace(self.record, state="superseded", eligible=False,
                      superseded_by=newer.occurrence)
        selector = replace(self.selector, occurrence=newer.occurrence,
                           revision=newer.revision)
        result = self.verify(selector=selector, authority=self.state(old, newer))
        self.assertEqual(result.status, "ACCEPTED")
        self.assertEqual(result.evidence.revision, newer.revision)

    def test_equal_bytes_do_not_merge_occurrences(self):
        other = replace(self.record, occurrence="synthetic-occurrence-B",
                        revision="synthetic-revision-B", series="synthetic-series-B")
        authority = self.state(self.record, other)
        first = self.verify(authority=authority)
        second = self.verify(selector=replace(self.selector, occurrence=other.occurrence,
                                              revision=other.revision), authority=authority)
        self.assertEqual((first.status, second.status), ("ACCEPTED", "ACCEPTED"))
        self.assertEqual(first.evidence.content_sha256, second.evidence.content_sha256)
        self.assertNotEqual(first.evidence.occurrence, second.evidence.occurrence)

    def test_missing_publication_identity(self):
        self.rejected("malformed-evidence", selector=replace(self.selector, occurrence=""))

    def test_wrong_publication_identity(self):
        self.rejected("publication-identity-mismatch",
                      selector=replace(self.selector, occurrence="synthetic-other"))

    def test_duplicate_conflicting_publication_identity(self):
        other = replace(self.record, revision="synthetic-revision-B")
        self.rejected("conflicting-publication-identity",
                      authority=self.state(self.record, other))

    def test_wrong_revision_identity(self):
        self.rejected("revision-identity-mismatch",
                      selector=replace(self.selector, revision="synthetic-other"))

    def test_revision_to_publication_mismatch(self):
        other = replace(self.record, occurrence="synthetic-occurrence-B",
                        revision="synthetic-revision-B", series="synthetic-series-B")
        self.rejected("revision-identity-mismatch",
                      selector=replace(self.selector, revision=other.revision),
                      authority=self.state(self.record, other))

    def test_tampered_artifact_bytes(self):
        self.rejected("artifact-bytes-mismatch", raw=self.raw + b" ")

    def test_content_identity_mismatch(self):
        self.rejected("content-identity-mismatch",
                      authority=self.state(replace(self.record, content_sha256="0" * 64)))

    def test_unsupported_contract_version(self):
        self.rejected("contract-version-unsupported",
                      authority=self.state(replace(self.record, contract_version="unsupported")))

    def test_publication_policy_mismatch(self):
        self.rejected("publication-policy-mismatch",
                      authority=self.state(replace(self.record, policy_version="unsupported")))

    def test_incorrect_producer_lineage(self):
        self.rejected("producer-lineage-mismatch", authority=self.state(replace(
            self.record, producer_snapshot_identity="synthetic-wrong-snapshot")))

    def test_missing_verified_admission(self):
        self.rejected("verified-admission-missing", admission=False)

    def test_unpublished_artifact(self):
        self.rejected("publication-ineligible", authority=self.state(replace(
            self.record, state="unpublished", eligible=False)))

    def test_withdrawn_publication(self):
        self.rejected("publication-withdrawn", authority=self.state(replace(
            self.record, state="withdrawn", eligible=False)))

    def test_superseded_publication(self):
        self.rejected("publication-superseded", authority=self.state(replace(
            self.record, state="superseded", eligible=False,
            superseded_by="synthetic-occurrence-B")))

    def test_stale_publication_evidence(self):
        self.rejected("stale-publication-evidence", selector=replace(
            self.selector, observed_generation="synthetic-generation-0"))

    def test_conflicting_current_revisions(self):
        other = replace(self.record, occurrence="synthetic-occurrence-B",
                        revision="synthetic-revision-B")
        self.rejected("conflicting-current-revisions",
                      authority=self.state(self.record, other))

    def test_historical_artifact_replay(self):
        newer = replace(self.record, occurrence="synthetic-occurrence-B",
                        revision="synthetic-revision-B")
        old = replace(self.record, state="superseded", eligible=False,
                      superseded_by=newer.occurrence)
        self.rejected("publication-superseded", authority=self.state(old, newer))

    def test_unavailable_authority_evidence(self):
        self.rejected("publication-evidence-unavailable", authority=self.state(
            self.record, available=False))

    def test_missing_authority_evidence(self):
        self.rejected("publication-evidence-missing", authority=False)

    def test_malformed_evidence(self):
        self.rejected("malformed-evidence", authority=self.state("malformed"))

    def test_previously_accepted_then_withdrawn(self):
        self.assertEqual(self.verify().status, "ACCEPTED")
        withdrawn = replace(self.record, state="withdrawn", eligible=False)
        self.rejected("publication-withdrawn", authority=self.state(withdrawn))

    def test_concurrent_state_change_rejects_stale_observation(self):
        changed = self.state(replace(self.record, state="withdrawn", eligible=False),
                             generation="synthetic-generation-2")
        self.rejected("stale-publication-evidence", authority=changed)

    def test_publication_does_not_confer_resource_or_view_authority(self):
        result = self.verify()
        self.assertEqual(result.status, "ACCEPTED")
        self.assertFalse(any(hasattr(result.evidence, field) for field in (
            "resource_identity", "business_entity", "principal_identity", "view_allow",
        )))

    def test_conflicting_revision_identity(self):
        other = replace(self.record, occurrence="synthetic-occurrence-B")
        self.rejected("conflicting-revision-state", authority=self.state(
            replace(self.record, state="superseded", eligible=False), other))


if __name__ == "__main__":
    unittest.main()
