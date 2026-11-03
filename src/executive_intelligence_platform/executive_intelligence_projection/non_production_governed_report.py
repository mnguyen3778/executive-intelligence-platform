"""NONPRODUCTION synthetic CEP report projection; never a release authority.

Fixture custody supplies Report/Engagement/Business Entity and revision facts
which current EIP artifacts do not contain. No production entry point imports
this module. A constructed candidate is always non-releasable here.
"""

from __future__ import annotations

from dataclasses import dataclass, fields

from executive_intelligence_platform.executive_intelligence_package import (
    EXECUTIVE_INTELLIGENCE_PACKAGE_CONTRACT_VERSION,
)
from executive_intelligence_platform.executive_intelligence_projection.projection import (
    EXECUTIVE_INTELLIGENCE_PROJECTION_CONTRACT_VERSION,
    ExecutiveIntelligenceProjection,
)
from executive_intelligence_platform.projection_delivery.verified_admission import (
    VerifiedAdmissionError,
    VerifiedSnapshotAdmission,
    VerifiedSnapshotGateway,
)
from executive_intelligence_platform.snapshot_compatibility.compatibility import (
    GOVERNED_ASSESSMENT_VERSION,
    GOVERNED_PACKAGE_CONTRACT_VERSION,
    GOVERNED_PACKAGE_LIMITATIONS,
    SUPPORTED_METHODOLOGY_VERSION,
    SUPPORTED_RESPONSE_CONTRACT_VERSION,
    _governed_conclusions_match_contract,
)
from executive_intelligence_platform.snapshot_derivation.derivation import (
    GOVERNED_CONTENT_DERIVATION_RULE_VERSION,
)


REPORT_CONTRACT_VERSION = "cep-governed-assessment-report-view-contract-v1"
SYNTHETIC_REPORT_IDENTITY_VERSION = "synthetic-report-resource-v1"
REPORT_LIMITATION = "nonproduction-report-projection-not-releasable"
REPORT_DISPLAY_PRODUCER_LIMITATIONS = (
    "service-decisions-not-implemented",
    "executive-narratives-not-implemented",
    "evidence-ingestion-not-implemented",
)


@dataclass(frozen=True)
class ReportSelector:
    """Untrusted exact selector; these strings establish no authority."""

    report: str
    engagement: str
    business_entity: str
    report_revision: str
    observed_generation: str


@dataclass(frozen=True)
class ReportEngagementLink:
    report: str
    engagement: str
    resource_class: str
    identity_version: str
    current: bool
    provenance: str


@dataclass(frozen=True)
class EngagementBusinessLink:
    engagement: str
    business_entity: str
    current: bool
    provenance: str


@dataclass(frozen=True)
class SourceRevisionEvidence:
    assessment_identity: str
    assessment_revision: str
    projection_revision: str
    snapshot_identity: str
    assessment_version: str
    methodology_version: str
    package_version: str
    projection_version: str
    current: bool
    projection_current: bool
    projection_eligible: bool
    provenance: str


@dataclass(frozen=True)
class ReportRevisionEvidence:
    report: str
    report_revision: str
    assessment_identity: str
    assessment_revision: str
    projection_revision: str
    contract_version: str
    current: bool
    projection_eligible: bool
    provenance: str


@dataclass(frozen=True)
class SyntheticReportAuthority:
    """One complete, trusted-local-fixture state generation; no live source."""

    generation: str
    available: bool
    report_links: tuple[ReportEngagementLink, ...]
    business_links: tuple[EngagementBusinessLink, ...]
    sources: tuple[SourceRevisionEvidence, ...]
    revisions: tuple[ReportRevisionEvidence, ...]


@dataclass(frozen=True)
class ReportProjection:
    """Internal candidate. Only display_safe() may be used for future views."""

    report: str
    engagement: str
    business_entity: str
    report_revision: str
    source_assessment_identity: str
    source_assessment_revision: str
    source_projection_revision: str
    producer_snapshot_identity: str
    contract_version: str
    methodology_version: str
    source_projection_version: str
    authority_generation: str
    summary: tuple[tuple[str, str], ...]
    risk: str
    confidence: str
    findings: tuple[tuple[str, str, str, str], ...]
    recommendations: tuple[tuple[str | None, str], ...]
    limitations: tuple[str, ...]

    def display_safe(self) -> dict[str, object]:
        """Return a fresh five-section candidate, without internal identity."""
        return {
            "Executive Summary": [
                {"section": key, "text": value} for key, value in self.summary
            ],
            "Risk and Confidence Context": {
                "riskClassification": self.risk,
                "confidenceClassification": self.confidence,
            },
            "Governed Findings": [
                {"findingReference": ref, "title": title,
                 "findingType": kind, "severityClassification": severity}
                for ref, title, kind, severity in self.findings
            ],
            "Recommendations": [
                {"findingReference": ref, "recommendationClassification": value}
                for ref, value in self.recommendations
            ],
            "Limitations": list(self.limitations),
        }


@dataclass(frozen=True)
class ReportProjectionResult:
    status: str
    reason: str | None = None
    projection: ReportProjection | None = None
    release_eligible: bool = False


def _reject(reason: str) -> ReportProjectionResult:
    return ReportProjectionResult("NOT_CONSTRUCTED", reason)


def _text(value: object) -> bool:
    return type(value) is str and bool(value.strip())


def construct_report(
    selector: object,
    authority: object,
    projection: object,
    *,
    admission: object,
    gateway: object,
) -> ReportProjectionResult:
    """Construct a local candidate only from verified source and fixture facts."""
    if (type(selector) is not ReportSelector or not all(_text(v) for v in (
            selector.report, selector.engagement, selector.business_entity,
            selector.report_revision, selector.observed_generation))):
        return _reject("invalid-selector")
    if type(authority) is not SyntheticReportAuthority:
        return _reject("authority-evidence-missing")
    if (not _text(authority.generation) or type(authority.available) is not bool or
            not all(type(v) is tuple for v in (
                authority.report_links, authority.business_links,
                authority.sources, authority.revisions))):
        return _reject("malformed-authority-evidence")
    if not authority.available:
        return _reject("authority-evidence-unavailable")
    if selector.observed_generation != authority.generation:
        return _reject("stale-authority-evidence")

    # Unique, independent R->E, E->B, source, and report-revision records.
    collections = (
        (authority.report_links, ReportEngagementLink, lambda v: v.report),
        (authority.business_links, EngagementBusinessLink, lambda v: v.engagement),
        (authority.sources, SourceRevisionEvidence, lambda v: v.assessment_identity),
        (authority.revisions, ReportRevisionEvidence,
         lambda v: (v.report, v.report_revision)),
    )
    for records, kind, key in collections:
        malformed_reason = ("malformed-source-evidence" if kind is SourceRevisionEvidence
                            else "malformed-authority-evidence")
        if any(type(record) is not kind for record in records):
            return _reject(malformed_reason)
        for record in records:
            for field in fields(record):
                value = getattr(record, field.name)
                if field.name in ("current", "projection_current", "projection_eligible"):
                    if type(value) is not bool:
                        return _reject(malformed_reason)
                elif not _text(value):
                    return _reject(malformed_reason)
        keys = [key(record) for record in records]
        if len(keys) != len(set(keys)):
            return _reject("conflicting-authority-evidence")
    report_links = [v for v in authority.report_links if v.report == selector.report]
    business_links = [v for v in authority.business_links if v.engagement == selector.engagement]
    revisions = [v for v in authority.revisions if v.report == selector.report]
    if not report_links or not business_links or not revisions or not authority.sources:
        return _reject("authority-evidence-missing")
    report_link, business_link = report_links[0], business_links[0]
    if (not all(_text(v) for v in (
            report_link.report, report_link.engagement, report_link.provenance,
            report_link.resource_class, report_link.identity_version,
            business_link.engagement, business_link.business_entity,
            business_link.provenance)) or
            type(report_link.current) is not bool or
            type(business_link.current) is not bool):
        return _reject("malformed-authority-evidence")
    if (report_link.resource_class != "REPORT" or
            report_link.identity_version != SYNTHETIC_REPORT_IDENTITY_VERSION):
        return _reject("unsupported-report-identity")
    if (report_link.engagement != selector.engagement or
            business_link.engagement != report_link.engagement):
        return _reject("conflicting-report-binding")
    if business_link.business_entity != selector.business_entity:
        return _reject("cross-business-entity-binding")
    if not report_link.current or not business_link.current:
        return _reject("stale-binding-evidence")

    current_revisions = [v for v in revisions if v.current]
    if len(current_revisions) != 1:
        return _reject("conflicting-report-revisions")
    report_revision = current_revisions[0]
    if report_revision.report_revision != selector.report_revision:
        return _reject("stale-report-revision")
    if (not all(_text(v) for v in (
            report_revision.report, report_revision.report_revision,
            report_revision.assessment_identity,
            report_revision.assessment_revision, report_revision.projection_revision,
            report_revision.contract_version, report_revision.provenance)) or
            type(report_revision.current) is not bool or
            type(report_revision.projection_eligible) is not bool):
        return _reject("malformed-authority-evidence")
    if report_revision.contract_version != REPORT_CONTRACT_VERSION:
        return _reject("unsupported-report-contract")
    if not report_revision.projection_eligible:
        return _reject("ineligible-report-projection")
    if len(authority.sources) != 1:
        return _reject("conflicting-source-revisions")
    source = authority.sources[0]
    if (not all(_text(v) for v in (
            source.assessment_identity, source.assessment_revision,
            source.projection_revision, source.snapshot_identity,
            source.assessment_version, source.methodology_version,
            source.package_version, source.projection_version,
            source.provenance)) or
            any(type(v) is not bool for v in (
                source.current, source.projection_current, source.projection_eligible))):
        return _reject("malformed-source-evidence")
    if (source.assessment_identity != report_revision.assessment_identity or
            source.assessment_revision != report_revision.assessment_revision or
            source.projection_revision != report_revision.projection_revision):
        return _reject("source-revision-mismatch")
    if report_revision.report_revision in (
            source.assessment_revision, source.projection_revision):
        return _reject("conflicting-report-revisions")
    if not source.current or not source.projection_current:
        return _reject("stale-source-evidence")
    if not source.projection_eligible:
        return _reject("ineligible-source-projection")
    if (source.assessment_version != GOVERNED_ASSESSMENT_VERSION or
            source.methodology_version != SUPPORTED_METHODOLOGY_VERSION or
            source.package_version != GOVERNED_PACKAGE_CONTRACT_VERSION or
            source.projection_version != EXECUTIVE_INTELLIGENCE_PROJECTION_CONTRACT_VERSION):
        return _reject("unsupported-source-version")
    if (type(projection) is not ExecutiveIntelligenceProjection or
            type(admission) is not VerifiedSnapshotAdmission or
            type(gateway) is not VerifiedSnapshotGateway):
        return _reject("verified-source-missing")

    try:
        gateway.verify_projection(admission, projection)
        snapshot = admission.snapshot
        source_package = projection.source_package
        derived = source_package.source_derived_artifact
        conclusions = derived.to_dict()["governedConclusions"]
        producer_package = snapshot["businessDecisionPackage"]
        versions = producer_package["versionMetadata"]
        if (not _governed_conclusions_match_contract(conclusions) or
                conclusions != producer_package["governedConclusions"]):
            return _reject("malformed-governed-content")
        if (source.snapshot_identity != admission.evidence.producer_snapshot_identity or
                source.snapshot_identity != projection.producer_snapshot_identity or
                source.snapshot_identity != source_package.producer_snapshot_identity or
                source.snapshot_identity != derived.producer_snapshot_identity or
                projection.lineage.producer_snapshot_identity != source.snapshot_identity):
            return _reject("source-lineage-mismatch")
        if (snapshot["responseContractVersion"] != SUPPORTED_RESPONSE_CONTRACT_VERSION or
                versions["contractVersion"] != source.package_version or
                versions["assessmentVersion"] != source.assessment_version or
                versions["methodologyVersion"] != source.methodology_version or
                projection.assessment_version != source.assessment_version or
                projection.methodology_version != source.methodology_version or
                projection.projection_contract_version != source.projection_version or
                source_package.package_contract_version !=
                EXECUTIVE_INTELLIGENCE_PACKAGE_CONTRACT_VERSION or
                derived.derivation_rule_version != GOVERNED_CONTENT_DERIVATION_RULE_VERSION):
            return _reject("unsupported-source-version")
        limitations = producer_package["limitations"]
        if tuple(limitations) != GOVERNED_PACKAGE_LIMITATIONS:
            return _reject("unsupported-source-limitations")
        summary = tuple(conclusions["executiveSummary"]["sectionText"].items())
        findings = tuple((v["findingId"], v["title"], v["findingType"],
                          v["severityClassification"])
                         for v in conclusions["severityAssignedFindings"])
        recommendations = tuple((v["findingId"], v["recommendationClassification"])
                                for v in conclusions["recommendations"])
        risk = conclusions["assessmentRisk"]["riskClassification"]
        confidence = conclusions["confidence"]["confidenceClassification"]
    except (VerifiedAdmissionError, ValueError, TypeError, KeyError, AttributeError):
        return _reject("verified-source-invalid")

    candidate = ReportProjection(
        selector.report, selector.engagement, selector.business_entity,
        report_revision.report_revision, source.assessment_identity,
        source.assessment_revision, source.projection_revision,
        source.snapshot_identity, REPORT_CONTRACT_VERSION,
        source.methodology_version, source.projection_version,
        authority.generation, summary, risk, confidence, findings,
        recommendations, REPORT_DISPLAY_PRODUCER_LIMITATIONS + (REPORT_LIMITATION,),
    )
    return ReportProjectionResult("CONSTRUCTED_NONPRODUCTION", projection=candidate)
