import copy
import sys
import unittest
from pathlib import Path
from types import MappingProxyType


EIP_ROOT = Path(__file__).resolve().parents[2]
ASSESSMENT_SERVICE_ROOT = EIP_ROOT.parent / "nguyen-ai-assessment-service"

sys.path.insert(0, str(EIP_ROOT / "src"))
sys.path.insert(0, str(ASSESSMENT_SERVICE_ROOT / "src"))

from assessment.business_decision_package import (  # noqa: E402
    BUSINESS_DECISION_PACKAGE_COMPONENT_VERSIONS,
    BUSINESS_DECISION_PACKAGE_CONTRACT_VERSION,
)
from assessment.executive_orchestration import (  # noqa: E402
    ValidatedCanonicalExecutiveAssessmentInput,
)
from assessment.executive_runtime import (  # noqa: E402
    EXECUTIVE_ASSESSMENT_VERSION,
    EXECUTIVE_RUNTIME_RESPONSE_CONTRACT_VERSION,
    NOT_PRODUCTION_AUTHORITATIVE,
)
from assessment.executive_snapshot_handoff import (  # noqa: E402
    produce_executive_assessment_snapshot,
)
from assessment.methodology_config import (  # noqa: E402
    BUSINESS_DECISION_METHODOLOGY,
    METHODOLOGY_VERSION,
)
from executive_intelligence_platform.snapshot_catalog import (  # noqa: E402
    SNAPSHOT_CATALOG_ADMISSION_POLICY_VERSION,
    SnapshotAdmissionMetadata,
    SnapshotCatalog,
    SnapshotCatalogEntry,
)
from executive_intelligence_platform.snapshot_derivation import (  # noqa: E402
    SNAPSHOT_DERIVATION_RULE_VERSION,
    SNAPSHOT_DERIVATION_RUNTIME_VERSION,
    SnapshotDerivationRequest,
    SnapshotDerivationRuntime,
)


PRODUCER_SNAPSHOT_IDENTITY = (
    "assessment-service:executive-assessment-snapshot:derivation-contract-v1"
)


def producer_answers(scale_value=4, numeric_value=100):
    return {
        question_id: (
            numeric_value
            if question.expected_answer_type == "numeric"
            else scale_value
        )
        for question_id, question in BUSINESS_DECISION_METHODOLOGY.questions.items()
    }


def producer_canonical_input(scale_value=4, numeric_value=100):
    return ValidatedCanonicalExecutiveAssessmentInput(
        assessment_version=EXECUTIVE_ASSESSMENT_VERSION,
        methodology_version=METHODOLOGY_VERSION,
        answers=producer_answers(scale_value, numeric_value),
    )


def producer_serialized_snapshot():
    production_result = produce_executive_assessment_snapshot(
        producer_canonical_input(scale_value=3, numeric_value=80)
    )
    if not production_result.is_success:
        raise AssertionError(
            "Assessment Service failed to produce serialized snapshot: "
            f"{production_result.failure}."
        )
    return production_result.serialized_snapshot


def admit_producer_snapshot(serialized_snapshot=None):
    snapshot = (
        producer_serialized_snapshot()
        if serialized_snapshot is None
        else serialized_snapshot
    )
    catalog = SnapshotCatalog()
    admission_result = catalog.admit(
        snapshot,
        producer_snapshot_identity=PRODUCER_SNAPSHOT_IDENTITY,
    )
    if not admission_result.accepted:
        raise AssertionError(
            "Executive Intelligence Platform failed to admit producer snapshot: "
            f"{issue_codes(admission_result)}."
        )
    return snapshot, catalog, admission_result


def issue_codes(result):
    return tuple(issue.code for issue in result.issues)


def incomplete_catalog_entry(snapshot_evidence):
    return SnapshotCatalogEntry(
        admission_metadata=SnapshotAdmissionMetadata(
            producer_snapshot_identity="",
            admission_policy_version=SNAPSHOT_CATALOG_ADMISSION_POLICY_VERSION,
            response_contract_version=EXECUTIVE_RUNTIME_RESPONSE_CONTRACT_VERSION,
            package_contract_version=BUSINESS_DECISION_PACKAGE_CONTRACT_VERSION,
            assessment_version=EXECUTIVE_ASSESSMENT_VERSION,
            methodology_version=METHODOLOGY_VERSION,
            source_component_ids=(),
            production_authority=NOT_PRODUCTION_AUTHORITATIVE,
            admission_sequence=1,
        ),
        snapshot_evidence=snapshot_evidence,
    )


def unadmitted_mutable_catalog_entry(serialized_snapshot):
    return SnapshotCatalogEntry(
        admission_metadata=SnapshotAdmissionMetadata(
            producer_snapshot_identity=PRODUCER_SNAPSHOT_IDENTITY,
            admission_policy_version=SNAPSHOT_CATALOG_ADMISSION_POLICY_VERSION,
            response_contract_version=EXECUTIVE_RUNTIME_RESPONSE_CONTRACT_VERSION,
            package_contract_version=BUSINESS_DECISION_PACKAGE_CONTRACT_VERSION,
            assessment_version=EXECUTIVE_ASSESSMENT_VERSION,
            methodology_version=METHODOLOGY_VERSION,
            source_component_ids=tuple(
                BUSINESS_DECISION_PACKAGE_COMPONENT_VERSIONS
            ),
            production_authority=NOT_PRODUCTION_AUTHORITATIVE,
            admission_sequence=1,
        ),
        snapshot_evidence=serialized_snapshot,
    )


class CrossRepositorySnapshotDerivationContractTests(unittest.TestCase):
    def test_admitted_assessment_service_snapshot_derives_successfully(self):
        serialized_snapshot, _catalog, admission_result = admit_producer_snapshot()
        runtime = SnapshotDerivationRuntime()

        result = runtime.derive(
            admission_result.entry,
            SnapshotDerivationRequest(),
        )

        self.assertTrue(result.derived)
        self.assertEqual(result.issues, ())
        self.assertIsNotNone(result.artifact)
        self.assertEqual(
            admission_result.entry.to_dict()["snapshotEvidence"],
            serialized_snapshot,
        )

    def test_derived_artifact_preserves_producer_versions_and_lineage(self):
        _serialized_snapshot, _catalog, admission_result = admit_producer_snapshot()

        result = SnapshotDerivationRuntime().derive(
            admission_result.entry,
            SnapshotDerivationRequest(),
        )

        artifact = result.artifact
        admission_metadata = admission_result.entry.admission_metadata
        producer_provenance = artifact.producer_provenance
        compatibility_metadata = artifact.compatibility_validation_metadata

        self.assertEqual(
            artifact.producer_snapshot_identity,
            PRODUCER_SNAPSHOT_IDENTITY,
        )
        self.assertEqual(
            artifact.snapshot_contract_version,
            EXECUTIVE_RUNTIME_RESPONSE_CONTRACT_VERSION,
        )
        self.assertEqual(
            artifact.assessment_version,
            EXECUTIVE_ASSESSMENT_VERSION,
        )
        self.assertEqual(
            artifact.methodology_version,
            METHODOLOGY_VERSION,
        )
        self.assertEqual(
            artifact.derivation_rule_version,
            SNAPSHOT_DERIVATION_RULE_VERSION,
        )
        self.assertEqual(
            artifact.derivation_runtime_version,
            SNAPSHOT_DERIVATION_RUNTIME_VERSION,
        )
        self.assertIs(artifact.catalog_admission_metadata, admission_metadata)
        self.assertEqual(
            admission_metadata.package_contract_version,
            BUSINESS_DECISION_PACKAGE_CONTRACT_VERSION,
        )
        self.assertEqual(
            admission_metadata.production_authority,
            NOT_PRODUCTION_AUTHORITATIVE,
        )
        self.assertEqual(
            compatibility_metadata.snapshot_contract_version,
            EXECUTIVE_RUNTIME_RESPONSE_CONTRACT_VERSION,
        )
        self.assertEqual(
            compatibility_metadata.assessment_version,
            EXECUTIVE_ASSESSMENT_VERSION,
        )
        self.assertEqual(
            compatibility_metadata.methodology_version,
            METHODOLOGY_VERSION,
        )
        self.assertEqual(
            producer_provenance.producer_snapshot_identity,
            PRODUCER_SNAPSHOT_IDENTITY,
        )
        self.assertEqual(
            producer_provenance.source_component_ids,
            tuple(admission_metadata.source_component_ids),
        )
        self.assertEqual(
            producer_provenance.production_authority,
            NOT_PRODUCTION_AUTHORITATIVE,
        )

    def test_derived_artifact_preserves_component_versions_and_evidence_lineage(self):
        _serialized_snapshot, _catalog, admission_result = admit_producer_snapshot()

        result = SnapshotDerivationRuntime().derive(
            admission_result.entry,
            SnapshotDerivationRequest(),
        )

        entry = admission_result.entry
        package = entry.snapshot_evidence["businessDecisionPackage"]
        version_metadata = package["versionMetadata"]

        self.assertTrue(result.derived)
        self.assertIsInstance(entry.snapshot_evidence, MappingProxyType)
        self.assertIsInstance(package, MappingProxyType)
        self.assertEqual(
            dict(version_metadata["componentVersions"]),
            dict(BUSINESS_DECISION_PACKAGE_COMPONENT_VERSIONS),
        )
        self.assertEqual(
            result.artifact.catalog_admission_metadata.source_component_ids,
            tuple(version_metadata["componentVersions"]),
        )

    def test_derivation_is_deterministic_for_same_admitted_snapshot(self):
        _serialized_snapshot, _catalog, admission_result = admit_producer_snapshot()
        runtime = SnapshotDerivationRuntime()
        request = SnapshotDerivationRequest()

        first_result = runtime.derive(admission_result.entry, request)
        second_result = runtime.derive(admission_result.entry, request)

        self.assertEqual(first_result, second_result)
        self.assertEqual(first_result.to_dict(), second_result.to_dict())

    def test_derivation_rejects_raw_producer_snapshot_fail_closed(self):
        serialized_snapshot = producer_serialized_snapshot()

        result = SnapshotDerivationRuntime().derive(
            serialized_snapshot,
            SnapshotDerivationRequest(),
        )

        self.assertFalse(result.derived)
        self.assertIsNone(result.artifact)
        self.assertEqual(issue_codes(result), ("invalid-catalog-entry",))

    def test_derivation_rejects_invalid_request_fail_closed(self):
        _serialized_snapshot, _catalog, admission_result = admit_producer_snapshot()

        result = SnapshotDerivationRuntime().derive(
            admission_result.entry,
            request=None,
        )

        self.assertFalse(result.derived)
        self.assertIsNone(result.artifact)
        self.assertEqual(issue_codes(result), ("invalid-derivation-request",))

    def test_derivation_rejects_unsupported_rule_fail_closed(self):
        _serialized_snapshot, _catalog, admission_result = admit_producer_snapshot()

        result = SnapshotDerivationRuntime().derive(
            admission_result.entry,
            SnapshotDerivationRequest(
                derivation_rule_version="unsupported-derivation-rule-v1"
            ),
        )

        self.assertFalse(result.derived)
        self.assertIsNone(result.artifact)
        self.assertEqual(issue_codes(result), ("unsupported-derivation-rule",))

    def test_derivation_rejects_malformed_unadmitted_catalog_entry_fail_closed(self):
        serialized_snapshot = producer_serialized_snapshot()

        result = SnapshotDerivationRuntime().derive(
            incomplete_catalog_entry(serialized_snapshot),
            SnapshotDerivationRequest(),
        )

        self.assertFalse(result.derived)
        self.assertIsNone(result.artifact)
        self.assertIn("incomplete-catalog-lineage", issue_codes(result))

    def test_derivation_rejects_unadmitted_mutable_catalog_entry_fail_closed(self):
        serialized_snapshot = producer_serialized_snapshot()

        result = SnapshotDerivationRuntime().derive(
            unadmitted_mutable_catalog_entry(serialized_snapshot),
            SnapshotDerivationRequest(),
        )

        self.assertFalse(result.derived)
        self.assertIsNone(result.artifact)
        self.assertEqual(issue_codes(result), ("missing-snapshot-evidence",))

    def test_derivation_rejects_catalog_entry_without_snapshot_evidence_fail_closed(
        self,
    ):
        result = SnapshotDerivationRuntime().derive(
            incomplete_catalog_entry(snapshot_evidence=None),
            SnapshotDerivationRequest(),
        )

        self.assertFalse(result.derived)
        self.assertIsNone(result.artifact)
        self.assertIn("incomplete-catalog-lineage", issue_codes(result))
        self.assertIn("missing-snapshot-evidence", issue_codes(result))

    def test_derivation_does_not_mutate_admitted_snapshot_or_catalog_entry(self):
        serialized_snapshot = producer_serialized_snapshot()
        before_admission = copy.deepcopy(serialized_snapshot)
        snapshot, _catalog, admission_result = admit_producer_snapshot(
            serialized_snapshot
        )
        entry_before_derivation = admission_result.entry.to_dict()

        SnapshotDerivationRuntime().derive(
            admission_result.entry,
            SnapshotDerivationRequest(),
        )

        self.assertEqual(snapshot, before_admission)
        self.assertEqual(admission_result.entry.to_dict(), entry_before_derivation)
        self.assertEqual(
            admission_result.entry.to_dict()["snapshotEvidence"],
            before_admission,
        )


if __name__ == "__main__":
    unittest.main()
