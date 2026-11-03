"""Phase 4C synthetic report projection tests; no client release."""

import sys
import unittest
from dataclasses import replace
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests" / "projection_delivery"))

import test_assessment_service_snapshot_delivery as source_fixture  # noqa: E402
from executive_intelligence_platform.executive_intelligence_projection.non_production_governed_report import (  # noqa: E402
    REPORT_CONTRACT_VERSION,
    SYNTHETIC_REPORT_IDENTITY_VERSION,
    EngagementBusinessLink,
    ReportEngagementLink,
    ReportRevisionEvidence,
    ReportSelector,
    SourceRevisionEvidence,
    SyntheticReportAuthority,
    construct_report,
)


class NonproductionGovernedReportTests(unittest.TestCase):
    def setUp(self):
        pipeline = source_fixture.governed_delivery_pipeline()
        self.snapshot = pipeline[0]
        self.projection = pipeline[5].projection
        self.gateway = pipeline[7]
        self.admission = pipeline[8]
        self.report_link = ReportEngagementLink(
            "synthetic-report-A", "synthetic-engagement-A", "REPORT",
            SYNTHETIC_REPORT_IDENTITY_VERSION, True, "synthetic-report-custody-A",
        )
        self.business_link = EngagementBusinessLink(
            "synthetic-engagement-A", "synthetic-business-A", True,
            "synthetic-business-custody-A",
        )
        self.source = SourceRevisionEvidence(
            "synthetic-assessment-A", "synthetic-assessment-revision-A",
            "synthetic-eip-projection-revision-A",
            self.admission.evidence.producer_snapshot_identity,
            self.projection.assessment_version, self.projection.methodology_version,
            self.snapshot["businessDecisionPackage"]["versionMetadata"]["contractVersion"],
            self.projection.projection_contract_version,
            True, True, True, "synthetic-source-custody-A",
        )
        self.revision = ReportRevisionEvidence(
            "synthetic-report-A", "synthetic-report-revision-A",
            self.source.assessment_identity,
            self.source.assessment_revision, self.source.projection_revision,
            REPORT_CONTRACT_VERSION, True, True, "synthetic-report-revision-custody-A",
        )
        self.authority = SyntheticReportAuthority(
            "synthetic-generation-A", True, (self.report_link,),
            (self.business_link,), (self.source,), (self.revision,),
        )
        self.selector = ReportSelector(
            "synthetic-report-A", "synthetic-engagement-A",
            "synthetic-business-A", "synthetic-report-revision-A",
            "synthetic-generation-A",
        )

    def run_report(self, selector=None, authority=None, projection=None,
                   admission=None, gateway=None):
        return construct_report(
            self.selector if selector is None else selector,
            self.authority if authority is None else authority,
            self.projection if projection is None else projection,
            admission=self.admission if admission is None else admission,
            gateway=self.gateway if gateway is None else gateway,
        )

    def authority_with(self, **changes):
        return replace(self.authority, **changes)

    def rejects(self, reason, **changes):
        result = self.run_report(**changes)
        self.assertEqual((result.status, result.reason, result.projection,
                          result.release_eligible),
                         ("NOT_CONSTRUCTED", reason, None, False))

    def test_valid_synthetic_projection_is_deterministic(self):
        first = self.run_report()
        self.assertEqual(first.status, "CONSTRUCTED_NONPRODUCTION")
        self.assertEqual(first, self.run_report())
        self.assertFalse(first.release_eligible)

    def test_exact_five_sections(self):
        result = self.run_report()
        self.assertEqual(tuple(result.projection.display_safe()), (
            "Executive Summary", "Risk and Confidence Context",
            "Governed Findings", "Recommendations", "Limitations",
        ))

    def test_unsupported_sections_excluded(self):
        display = self.run_report().projection.display_safe()
        self.assertNotIn("Assessment Classification", display)
        self.assertNotIn("Priority Recommendations", display)
        self.assertNotIn("Assessment Progress", display)

    def test_source_meaning_preserved(self):
        governed = self.snapshot["businessDecisionPackage"]["governedConclusions"]
        display = self.run_report().projection.display_safe()
        self.assertEqual([(v["section"], v["text"]) for v in
                          display["Executive Summary"]],
                         list(governed["executiveSummary"]["sectionText"].items()))
        self.assertEqual(display["Risk and Confidence Context"], {
            "riskClassification": governed["assessmentRisk"]["riskClassification"],
            "confidenceClassification": governed["confidence"]["confidenceClassification"],
        })
        self.assertEqual([v["severityClassification"] for v in
                          display["Governed Findings"]],
                         [v["severityClassification"] for v in
                          governed["severityAssignedFindings"]])
        self.assertEqual([v["recommendationClassification"] for v in
                          display["Recommendations"]],
                         [v["recommendationClassification"] for v in
                          governed["recommendations"]])
        self.assertTrue(set(display["Limitations"][:-1]).issubset(
            self.snapshot["businessDecisionPackage"]["limitations"]))

    def test_no_independent_scoring(self):
        display = self.run_report().projection.display_safe()
        keys = set(display)
        for section in display.values():
            if isinstance(section, list):
                keys.update(key for item in section if isinstance(item, dict)
                            for key in item)
            elif isinstance(section, dict):
                keys.update(section)
        self.assertTrue(keys.isdisjoint((
            "score", "readiness", "priorityScore", "findingCount",
        )))

    def test_missing_report_identity(self):
        self.rejects("invalid-selector", selector=replace(self.selector, report=""))

    def test_missing_engagement_identity(self):
        self.rejects("invalid-selector", selector=replace(self.selector, engagement=""))

    def test_missing_business_entity_identity(self):
        self.rejects("invalid-selector", selector=replace(self.selector,
                                                           business_entity=""))

    def test_conflicting_report_engagement_binding(self):
        link = replace(self.report_link, engagement="synthetic-engagement-B")
        self.rejects("conflicting-report-binding", authority=self.authority_with(
            report_links=(link,)))

    def test_cross_tenant_binding(self):
        link = replace(self.business_link, business_entity="synthetic-business-B")
        self.rejects("cross-business-entity-binding", authority=self.authority_with(
            business_links=(link,)))

    def test_duplicate_binding_fails_closed(self):
        self.rejects("conflicting-authority-evidence", authority=self.authority_with(
            report_links=(self.report_link, replace(self.report_link,
                                                   engagement="synthetic-engagement-B"))))

    def test_unsupported_identity_version(self):
        self.rejects("unsupported-report-identity", authority=self.authority_with(
            report_links=(replace(self.report_link, identity_version="unsupported"),)))

    def test_unsupported_report_contract(self):
        self.rejects("unsupported-report-contract", authority=self.authority_with(
            revisions=(replace(self.revision, contract_version="unsupported"),)))

    def test_missing_source_revision(self):
        self.rejects("malformed-source-evidence", authority=self.authority_with(
            sources=(replace(self.source, assessment_revision=""),)))

    def test_conflicting_source_revision(self):
        self.rejects("source-revision-mismatch", authority=self.authority_with(
            sources=(replace(self.source, assessment_revision="synthetic-other"),)))

    def test_conflicting_current_report_revisions(self):
        other = replace(self.revision, report_revision="synthetic-report-revision-B")
        self.rejects("conflicting-report-revisions", authority=self.authority_with(
            revisions=(self.revision, other)))

    def test_report_revision_cannot_be_source_revision(self):
        revised = replace(self.revision,
                          report_revision=self.source.assessment_revision)
        selected = replace(self.selector, report_revision=revised.report_revision)
        self.rejects("conflicting-report-revisions", selector=selected,
                     authority=self.authority_with(revisions=(revised,)))

    def test_stale_source_evidence(self):
        self.rejects("stale-source-evidence", authority=self.authority_with(
            sources=(replace(self.source, current=False),)))

    def test_missing_currentness(self):
        self.rejects("malformed-source-evidence", authority=self.authority_with(
            sources=(replace(self.source, projection_current=None),)))

    def test_stale_observed_generation(self):
        self.rejects("stale-authority-evidence", selector=replace(
            self.selector, observed_generation="synthetic-old-generation"))

    def test_unsupported_source_version(self):
        self.rejects("unsupported-source-version", authority=self.authority_with(
            sources=(replace(self.source, package_version="unsupported"),)))

    def test_ineligible_source_projection(self):
        self.rejects("ineligible-source-projection", authority=self.authority_with(
            sources=(replace(self.source, projection_eligible=False),)))

    def test_ineligible_report_projection(self):
        self.rejects("ineligible-report-projection", authority=self.authority_with(
            revisions=(replace(self.revision, projection_eligible=False),)))

    def test_missing_required_lineage(self):
        self.rejects("source-lineage-mismatch", authority=self.authority_with(
            sources=(replace(self.source, snapshot_identity="synthetic-other-snapshot"),)))

    def test_malformed_source_content(self):
        source_package = self.projection.source_package
        derived = source_package.source_derived_artifact
        conclusions = derived.to_dict()["governedConclusions"]
        conclusions.pop("executiveSummary")
        malformed = replace(
            self.projection,
            source_package=replace(source_package, source_derived_artifact=replace(
                derived, governed_conclusions=conclusions)),
        )
        self.rejects("verified-source-invalid", projection=malformed)

    def test_internal_evidence_excluded_from_display(self):
        display = self.run_report().projection.display_safe()
        text = str(display)
        for forbidden in ("synthetic-report-A", "synthetic-business-A",
                          "synthetic-assessment-revision-A", "snapshotDigest",
                          "sourceReferences", "decisionIdentifier", "sourcePackage",
                          "businessDecisionPackage", "audit"):
            self.assertNotIn(forbidden, text)
        self.assertNotIn("persistence-not-implemented", display["Limitations"])
        self.assertNotIn("api-exposure-of-snapshot-consumers-not-implemented",
                         display["Limitations"])

    def test_report_dashboard_identity_distinct(self):
        report = self.run_report().projection
        self.assertEqual(self.report_link.resource_class, "REPORT")
        self.assertNotEqual(report.contract_version,
                            self.projection.projection_contract_version)
        self.assertNotEqual(report.report_revision, report.source_assessment_revision)
        self.assertNotEqual(report.report_revision, report.source_projection_revision)

    def test_no_authorization_allow(self):
        result = self.run_report()
        self.assertFalse(result.release_eligible)
        self.assertFalse(hasattr(result, "view_allow"))
        self.assertFalse(hasattr(result.projection, "entitlement"))

    def test_no_production_release_claim(self):
        result = self.run_report()
        self.assertIn("nonproduction-report-projection-not-releasable",
                      result.projection.display_safe()["Limitations"])
        self.assertFalse(result.release_eligible)

    def test_no_download_or_export(self):
        result = self.run_report()
        self.assertFalse(hasattr(result.projection, "download"))
        self.assertFalse(hasattr(result.projection, "export"))
        self.assertFalse(hasattr(result.projection, "pdf"))

    def test_unverified_source_rejected(self):
        self.rejects("verified-source-missing", admission=False)

    def test_caller_business_assertion_cannot_override_custody(self):
        self.rejects("cross-business-entity-binding", selector=replace(
            self.selector, business_entity="synthetic-browser-business"))


if __name__ == "__main__":
    unittest.main()
