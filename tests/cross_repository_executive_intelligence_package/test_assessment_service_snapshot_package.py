import copy
import sys
import unittest
from pathlib import Path


EIP_ROOT = Path(__file__).resolve().parents[2]
ASSESSMENT_SERVICE_ROOT = EIP_ROOT.parent / "nguyen-ai-assessment-service"

sys.path.insert(0, str(EIP_ROOT / "src"))
sys.path.insert(0, str(ASSESSMENT_SERVICE_ROOT / "src"))

from assessment.business_decision_package import (  # noqa: E402
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
from executive_intelligence_platform.executive_intelligence_package import (  # noqa: E402
    EXECUTIVE_INTELLIGENCE_PACKAGE_ASSEMBLY_RULE_VERSION,
    EXECUTIVE_INTELLIGENCE_PACKAGE_CONTRACT_VERSION,
    ExecutiveIntelligencePackageAssembler,
    ExecutiveIntelligencePackageRequest,
)
from executive_intelligence_platform.snapshot_catalog import (  # noqa: E402
    SnapshotCatalog,
)
from executive_intelligence_platform.snapshot_compatibility import (  # noqa: E402
    validate_snapshot_compatibility,
)
from executive_intelligence_platform.snapshot_derivation import (  # noqa: E402
    SNAPSHOT_DERIVATION_RULE_VERSION,
    SNAPSHOT_DERIVATION_RUNTIME_VERSION,
    SnapshotCompatibilityValidationMetadata,
    SnapshotDerivationRequest,
    SnapshotDerivationRuntime,
    SnapshotDerivedArtifact,
    SnapshotProducerProvenance,
)


PRODUCER_SNAPSHOT_IDENTITY = (
    "assessment-service:executive-assessment-snapshot:package-contract-v1"
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


def produce_package_pipeline(serialized_snapshot=None):
    snapshot = (
        producer_serialized_snapshot()
        if serialized_snapshot is None
        else serialized_snapshot
    )
    compatibility_result = validate_snapshot_compatibility(snapshot)
    if not compatibility_result.is_valid:
        raise AssertionError(
            "Executive Intelligence Platform rejected producer snapshot: "
            f"{issue_codes(compatibility_result)}."
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

    derivation_result = SnapshotDerivationRuntime().derive(
        admission_result.entry,
        SnapshotDerivationRequest(),
    )
    if not derivation_result.derived:
        raise AssertionError(
            "Executive Intelligence Platform failed to derive producer snapshot: "
            f"{issue_codes(derivation_result)}."
        )

    package_result = ExecutiveIntelligencePackageAssembler().assemble(
        ExecutiveIntelligencePackageRequest(),
        derivation_result.artifact,
    )

    return snapshot, admission_result, derivation_result, package_result


def issue_codes(result):
    return tuple(issue.code for issue in result.issues)


def contains_key(value, key_name):
    if isinstance(value, dict):
        return key_name in value or any(
            contains_key(child, key_name) for child in value.values()
        )
    if isinstance(value, list):
        return any(contains_key(child, key_name) for child in value)
    return False


class CrossRepositoryExecutiveIntelligencePackageContractTests(unittest.TestCase):
    def test_assessment_service_snapshot_progresses_to_package(self):
        _snapshot, _admission_result, _derivation_result, package_result = (
            produce_package_pipeline()
        )

        self.assertTrue(package_result.packaged)
        self.assertEqual(package_result.issues, ())
        self.assertIsNotNone(package_result.package)
        self.assertEqual(
            package_result.package.package_contract_version,
            EXECUTIVE_INTELLIGENCE_PACKAGE_CONTRACT_VERSION,
        )
        self.assertEqual(
            package_result.package.package_assembly_rule_version,
            EXECUTIVE_INTELLIGENCE_PACKAGE_ASSEMBLY_RULE_VERSION,
        )

    def test_package_preserves_versions_identity_and_lineage(self):
        _snapshot, admission_result, derivation_result, package_result = (
            produce_package_pipeline()
        )

        package = package_result.package
        lineage = package.lineage
        admission_metadata = admission_result.entry.admission_metadata

        self.assertEqual(
            package.producer_snapshot_identity,
            PRODUCER_SNAPSHOT_IDENTITY,
        )
        self.assertEqual(
            package.snapshot_contract_version,
            EXECUTIVE_RUNTIME_RESPONSE_CONTRACT_VERSION,
        )
        self.assertEqual(
            package.assessment_version,
            EXECUTIVE_ASSESSMENT_VERSION,
        )
        self.assertEqual(package.methodology_version, METHODOLOGY_VERSION)
        self.assertEqual(
            package.derivation_rule_version,
            SNAPSHOT_DERIVATION_RULE_VERSION,
        )
        self.assertEqual(
            package.derivation_runtime_version,
            SNAPSHOT_DERIVATION_RUNTIME_VERSION,
        )
        self.assertIs(package.source_derived_artifact, derivation_result.artifact)
        self.assertEqual(
            lineage.producer_snapshot_identity,
            PRODUCER_SNAPSHOT_IDENTITY,
        )
        self.assertEqual(
            lineage.snapshot_contract_version,
            EXECUTIVE_RUNTIME_RESPONSE_CONTRACT_VERSION,
        )
        self.assertEqual(lineage.assessment_version, EXECUTIVE_ASSESSMENT_VERSION)
        self.assertEqual(lineage.methodology_version, METHODOLOGY_VERSION)
        self.assertEqual(
            lineage.derivation_rule_version,
            SNAPSHOT_DERIVATION_RULE_VERSION,
        )
        self.assertEqual(
            lineage.derivation_runtime_version,
            SNAPSHOT_DERIVATION_RUNTIME_VERSION,
        )
        self.assertIs(lineage.catalog_admission_metadata, admission_metadata)
        self.assertEqual(
            lineage.catalog_admission_metadata.package_contract_version,
            BUSINESS_DECISION_PACKAGE_CONTRACT_VERSION,
        )
        self.assertEqual(
            lineage.catalog_admission_metadata.production_authority,
            NOT_PRODUCTION_AUTHORITATIVE,
        )
        self.assertEqual(
            lineage.producer_provenance.producer_snapshot_identity,
            PRODUCER_SNAPSHOT_IDENTITY,
        )
        self.assertEqual(
            lineage.producer_provenance.production_authority,
            NOT_PRODUCTION_AUTHORITATIVE,
        )
        self.assertEqual(
            lineage.producer_provenance.source_component_ids,
            tuple(admission_metadata.source_component_ids),
        )

    def test_package_preserves_immutable_evidence_lineage_without_embedding_truth(self):
        snapshot, admission_result, derivation_result, package_result = (
            produce_package_pipeline()
        )

        package_data = package_result.package.to_dict()
        snapshot_evidence = admission_result.entry.to_dict()["snapshotEvidence"]

        self.assertEqual(snapshot_evidence, snapshot)
        self.assertEqual(
            package_result.package.source_derived_artifact,
            derivation_result.artifact,
        )
        self.assertFalse(contains_key(package_data, "businessDecisionPackage"))
        self.assertFalse(contains_key(package_data, "decisionEvaluation"))
        self.assertFalse(contains_key(package_data, "businessReadinessSnapshot"))
        self.assertFalse(contains_key(package_data, "confidenceEvaluation"))
        self.assertFalse(
            contains_key(package_data, "recommendationPriorityEvaluation")
        )

    def test_package_assembly_does_not_mutate_producer_snapshot_or_pipeline_artifacts(
        self,
    ):
        serialized_snapshot = producer_serialized_snapshot()
        snapshot_before = copy.deepcopy(serialized_snapshot)

        snapshot, admission_result, derivation_result, _package_result = (
            produce_package_pipeline(serialized_snapshot)
        )
        catalog_entry_before = admission_result.entry.to_dict()
        derived_artifact_before = derivation_result.artifact.to_dict()

        ExecutiveIntelligencePackageAssembler().assemble(
            ExecutiveIntelligencePackageRequest(),
            derivation_result.artifact,
        )

        self.assertEqual(snapshot, snapshot_before)
        self.assertEqual(admission_result.entry.to_dict(), catalog_entry_before)
        self.assertEqual(
            derivation_result.artifact.to_dict(),
            derived_artifact_before,
        )
        self.assertEqual(
            admission_result.entry.to_dict()["snapshotEvidence"],
            snapshot_before,
        )

    def test_package_output_is_deterministic_for_same_derived_artifact(self):
        _snapshot, _admission_result, derivation_result, _package_result = (
            produce_package_pipeline()
        )
        request = ExecutiveIntelligencePackageRequest()
        assembler = ExecutiveIntelligencePackageAssembler()

        first_result = assembler.assemble(request, derivation_result.artifact)
        second_result = assembler.assemble(request, derivation_result.artifact)

        self.assertEqual(first_result, second_result)
        self.assertEqual(first_result.to_dict(), second_result.to_dict())

    def test_incompatible_producer_snapshot_fails_before_package_assembly(self):
        serialized_snapshot = producer_serialized_snapshot()
        serialized_snapshot["responseContractVersion"] = "unsupported-contract"

        compatibility_result = validate_snapshot_compatibility(serialized_snapshot)
        catalog_result = SnapshotCatalog().admit(
            serialized_snapshot,
            producer_snapshot_identity=PRODUCER_SNAPSHOT_IDENTITY,
        )

        self.assertFalse(compatibility_result.is_valid)
        self.assertIn(
            "unsupported-response-contract-version",
            issue_codes(compatibility_result),
        )
        self.assertFalse(catalog_result.accepted)
        self.assertIsNone(catalog_result.entry)
        self.assertIn("incompatible-snapshot", issue_codes(catalog_result))

    def test_package_rejects_raw_snapshot_fail_closed(self):
        result = ExecutiveIntelligencePackageAssembler().assemble(
            ExecutiveIntelligencePackageRequest(),
            producer_serialized_snapshot(),
        )

        self.assertFalse(result.packaged)
        self.assertIsNone(result.package)
        self.assertEqual(issue_codes(result), ("invalid-derived-artifact",))

    def test_package_rejects_unadmitted_catalog_entry_fail_closed(self):
        _snapshot, admission_result, _derivation_result, _package_result = (
            produce_package_pipeline()
        )

        result = ExecutiveIntelligencePackageAssembler().assemble(
            ExecutiveIntelligencePackageRequest(),
            admission_result.entry,
        )

        self.assertFalse(result.packaged)
        self.assertIsNone(result.package)
        self.assertEqual(issue_codes(result), ("invalid-derived-artifact",))

    def test_package_rejects_underived_derivation_result_fail_closed(self):
        _snapshot, _admission_result, derivation_result, _package_result = (
            produce_package_pipeline()
        )

        result = ExecutiveIntelligencePackageAssembler().assemble(
            ExecutiveIntelligencePackageRequest(),
            derivation_result,
        )

        self.assertFalse(result.packaged)
        self.assertIsNone(result.package)
        self.assertEqual(issue_codes(result), ("invalid-derived-artifact",))

    def test_package_rejects_inconsistent_derived_artifact_fail_closed(self):
        _snapshot, _admission_result, derivation_result, _package_result = (
            produce_package_pipeline()
        )
        source = derivation_result.artifact
        inconsistent_artifact = SnapshotDerivedArtifact(
            producer_snapshot_identity=source.producer_snapshot_identity,
            snapshot_contract_version="different-snapshot-contract",
            assessment_version=source.assessment_version,
            methodology_version=source.methodology_version,
            catalog_admission_metadata=source.catalog_admission_metadata,
            compatibility_validation_metadata=(
                SnapshotCompatibilityValidationMetadata(
                    snapshot_contract_version=source.snapshot_contract_version,
                    assessment_version=source.assessment_version,
                    methodology_version=source.methodology_version,
                )
            ),
            producer_provenance=SnapshotProducerProvenance(
                producer_snapshot_identity=source.producer_snapshot_identity,
                source_component_ids=source.producer_provenance.source_component_ids,
                production_authority=source.producer_provenance.production_authority,
            ),
            derivation_rule_version=source.derivation_rule_version,
            derivation_runtime_version=source.derivation_runtime_version,
        )

        result = ExecutiveIntelligencePackageAssembler().assemble(
            ExecutiveIntelligencePackageRequest(),
            inconsistent_artifact,
        )

        self.assertFalse(result.packaged)
        self.assertIsNone(result.package)
        self.assertIn("inconsistent-derived-artifact-lineage", issue_codes(result))


if __name__ == "__main__":
    unittest.main()
