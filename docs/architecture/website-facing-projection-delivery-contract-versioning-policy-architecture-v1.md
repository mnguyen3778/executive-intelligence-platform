# Website-Facing Projection Delivery Contract and Versioning Policy Architecture v1

## 1. Status

Status: Architecture proposed for review

Owner: Executive Intelligence Platform

Mode: Architecture only

Repository: `executive-intelligence-platform`

This document defines the Executive Intelligence Platform-owned Website-facing Projection Delivery Contract and Versioning Policy Architecture required before any governed Website implementation may begin.

This document does not authorize implementation, application code, APIs, transport, persistence, infrastructure, deployment, runtime behavior changes, dashboard implementation, reporting, projection behavior changes, or Assessment Service changes.

## 2. Reviewed Architecture Sources

This architecture was produced after reviewing:

- `AGENTS.md`
- `README.md`
- `docs/governance/repository-governance-v1.md`
- `docs/architecture/executive-intelligence-projection-architecture-v1.md`
- `docs/architecture/executive-intelligence-package-contract-v1.md`
- Website `docs/architecture/phase-iv-executive-dashboard-architecture-v1.md`
- Website `docs/architecture/website-projection-delivery-contract-architecture-v1.md`

These documents establish the governing boundary:

```text
Assessment Service
  -> ExecutiveAssessmentSnapshot
  -> Executive Intelligence Platform
  -> ExecutiveIntelligenceProjection
  -> Website-facing Projection Delivery Contract
  -> Website Executive Dashboard rendering
```

## 3. Purpose

The Website-facing Projection Delivery Contract is the governed publication boundary from the Executive Intelligence Platform to the Website.

Its purpose is to define how an approved `ExecutiveIntelligenceProjection` may be represented for Website consumption while preserving:

- producer / consumer isolation
- immutable evidence
- deterministic behavior
- end-to-end lineage
- fail-closed validation
- versioned contracts
- governance-first engineering
- repository ownership

The delivery contract exists because the Website must not consume raw upstream platform objects. The Website receives only an EIP-published, Website-facing delivery representation that contains explicit eligibility, version, lineage, limitation, classification, compatibility, and fail-closed indicators.

## 4. Architectural Decision 006

**Decision:** The Executive Intelligence Platform owns the Website-facing Projection Delivery Contract and its versioning policy.

**Status:** Proposed for architectural review.

**Context:** Phase III verified the producer-to-consumer pipeline through Executive Intelligence Projection. The Website has approved dashboard and projection delivery architecture, but implementation cannot begin until the Executive Intelligence Platform defines the authoritative delivery contract and versioning policy it will publish.

**Decision Detail:** The Executive Intelligence Platform will define a deterministic Website-facing delivery contract over approved `ExecutiveIntelligenceProjection` artifacts. The contract will publish only safe, allowlisted, versioned, lineage-preserving fields required by the Website dashboard. The contract will include explicit publication eligibility, publication status, freshness, compatibility, classification, limitation, and fail-closed reason indicators. The Website may recognize the delivery contract and render eligible content, but must not make upstream compatibility, eligibility, projection, package, derivation, catalog, snapshot, or assessment-truth decisions.

**Consequences:**

- EIP remains the owner of projection production, publication eligibility, compatibility decisions, delivery contract versioning, and projection publication status.
- The Website remains a deterministic presentation consumer only.
- Website implementation must fail closed unless the delivery contract explicitly marks content eligible for rendering.
- Version incompatibility, stale projection state, missing lineage, missing limitations, or prohibited fields must block authoritative Website rendering.
- No API, transport, persistence, or runtime mechanism is selected by this architecture.

## 5. Repository Ownership

### Assessment Service Ownership

The Assessment Service owns:

- assessment truth
- `ExecutiveAssessmentSnapshot`
- methodology
- `BusinessDecisionPackage`
- snapshot serialization
- deterministic assessment outputs
- production-authority semantics

The delivery contract may reference Assessment Service concepts only through lineage and version fields already preserved by EIP-owned projection artifacts. This repository must not redefine, modify, validate, serialize, or recompute Assessment Service-owned truth in this contract.

### Executive Intelligence Platform Ownership

The Executive Intelligence Platform owns:

- `ExecutiveIntelligenceProjection`
- projection production
- projection publication
- Website-facing delivery contract
- delivery contract versioning
- publication eligibility decisions
- publication status decisions
- projection freshness semantics
- projection compatibility indicators
- stable fail-closed reason codes
- delivery field allowlisting from platform-owned projection output

EIP is the producer of Website-facing projection delivery representations. EIP is not the producer of `ExecutiveAssessmentSnapshot` artifacts or Assessment Service business truth.

### Website Ownership

The Website owns:

- rendering
- visualization
- layout
- navigation
- deterministic presentation
- accessible dashboard behavior
- fail-closed UI behavior

The Website must never:

- validate snapshots
- inspect raw `BusinessDecisionPackage` bodies
- inspect raw Executive Intelligence Packages
- inspect raw derived artifacts
- inspect raw catalog entries
- create projections
- determine publication eligibility
- determine compatibility
- recompute assessment truth
- infer missing projection fields
- repair delivery contract violations

## 6. Delivery Contract Boundary

The Website-facing Projection Delivery Contract is a platform-owned publication envelope over an approved `ExecutiveIntelligenceProjection`.

The delivery contract is not:

- an API
- a transport protocol
- a persistence model
- a database schema
- a dashboard implementation
- a reporting model
- a replacement projection model
- an Assessment Service contract
- a snapshot serialization contract

The contract must be produced only after the source projection has been generated, validated for projection integrity, evaluated for publication eligibility, and marked with deterministic publication and compatibility indicators.

The Website must consume only the delivery representation. It must not reach behind the delivery contract to inspect platform runtime objects or Assessment Service artifacts.

## 7. Delivery Contract Version Identity

The delivery contract must carry a stable version identity.

The version identity for this architecture is:

```text
website-projection-delivery-contract-v1
```

This identifier is owned by the Executive Intelligence Platform.

The version identity must be present in every delivery representation. It must not be inferred from:

- route names
- file names
- deployment versions
- timestamps
- package versions
- projection versions
- dashboard UI versions
- Website build versions
- cache keys
- transport metadata

Delivery contract versioning is distinct from:

- `ExecutiveAssessmentSnapshot` contract versioning
- `BusinessDecisionPackage` contract versioning
- assessment versioning
- methodology versioning
- `ExecutiveIntelligencePackage` contract versioning
- `ExecutiveIntelligenceProjection` contract versioning
- future API versioning
- Website application versioning

## 8. Version Compatibility Policy

Version compatibility decisions belong to EIP.

The delivery contract must expose compatibility as an explicit platform-owned decision. The Website may recognize whether a delivery contract version is supported by its rendering implementation, but it must not compute upstream compatibility.

Required compatibility states:

- `compatible`
- `incompatible`
- `unsupported_version`
- `lineage_incomplete`
- `restricted`
- `stale`
- `superseded`
- `unpublished`
- `unknown`

Only `compatible` may contribute to authoritative Website rendering, and only when all other eligibility indicators are passing.

Compatibility must fail closed when:

- the delivery contract version is missing
- the delivery contract version is unsupported
- the projection contract version is missing or unsupported
- the package contract version is missing or unsupported
- snapshot lineage version references are missing
- assessment or methodology version references are missing
- component version references required by governance are unavailable
- publication eligibility is absent or ambiguous
- lineage or limitation visibility is incomplete

Forward compatibility is denied by default. Backward compatibility requires an explicit EIP-owned compatibility decision and a documented allow policy before Website rendering may treat older delivery contract versions as eligible.

## 9. Publication Eligibility Model

Publication eligibility is the EIP-owned decision that determines whether a projection may be delivered to the Website as governed dashboard input.

The delivery contract must include explicit eligibility indicators:

- `projection_eligible_for_dashboard`
- `publication_state`
- `compatibility_state`
- `authorization_scope_state`
- `lineage_state`
- `limitation_visibility_state`
- `freshness_state`
- `classification_state`
- `content_source_type`

Governed Website rendering requires all of the following:

- `projection_eligible_for_dashboard: true`
- `publication_state: published`
- `compatibility_state: compatible`
- `authorization_scope_state: authorized`
- `lineage_state: complete`
- `limitation_visibility_state: visible`
- `freshness_state: current`
- `classification_state: approved`
- `content_source_type: governed_projection`

If any indicator is missing, ambiguous, or non-passing, the delivery contract must mark the response ineligible and include a stable fail-closed reason code.

Eligibility decisions must not be delegated to the Website.

## 10. Publication Status Model

Publication status describes the governed release state of a projection delivery representation.

Allowed publication states:

- `draft`
- `pending_review`
- `published`
- `restricted`
- `revoked`
- `superseded`
- `expired`
- `unpublished`

Only `published` may be eligible for authoritative Website rendering.

All other states must fail closed unless a future approved architecture defines a limited non-authoritative metadata-only display mode.

Publication status must be deterministic for the same projection, governance state, compatibility state, freshness state, lineage state, limitation state, classification state, and publication policy version.

Publication status must not be replaced by Website route state, UI state, authentication state, cache state, browser state, or feature flags.

## 11. Projection Freshness Semantics

Projection freshness indicates whether the delivered projection remains the current governed representation for Website rendering.

Allowed freshness states:

- `current`
- `stale`
- `superseded`
- `expired`
- `unknown`

Only `current` may be eligible for authoritative Website rendering.

Freshness must be based on EIP-owned publication governance, not Website cache age alone. Future implementation may include timestamps, sequence numbers, or replacement references only after approved implementation scope defines them. This architecture does not choose a clock source, storage model, cache model, event model, or API mechanism.

The Website may display a fail-closed not-current state when freshness is not `current`. It must not treat stale or cached content as authoritative by local inference.

## 12. Stable Fail-Closed Reason Codes

Every delivery failure or ineligible state must expose a stable reason code intended for downstream automation, audit, and deterministic Website UI behavior.

Reason codes are stable identifiers. They must not depend on message text, localization, display labels, exception strings, stack traces, route names, or transport details.

Initial EIP-owned reason code registry:

| Code | Meaning |
| --- | --- |
| `delivery-contract-version-missing` | Delivery contract version is absent. |
| `delivery-contract-version-unsupported` | Delivery contract version is not supported. |
| `projection-reference-missing` | Projection identity or projection reference is absent. |
| `projection-contract-version-unsupported` | Projection contract version is unsupported. |
| `projection-ineligible` | Projection is not eligible for Website dashboard rendering. |
| `publication-state-not-published` | Publication state is not `published`. |
| `compatibility-state-not-compatible` | Compatibility state is not `compatible`. |
| `authorization-scope-not-authorized` | Authorization scope is not marked authorized for delivery. |
| `lineage-state-incomplete` | Required lineage is missing, incomplete, or ambiguous. |
| `limitations-not-visible` | Required limitation indicators are missing or not visible. |
| `freshness-state-not-current` | Projection freshness is stale, superseded, expired, or unknown. |
| `classification-not-approved` | Field or response classification is missing or not approved for Website delivery. |
| `content-source-type-invalid` | Content source type is missing, unknown, or mixed. |
| `prohibited-field-present` | Delivery representation contains a prohibited field. |
| `delivery-payload-malformed` | Delivery representation is structurally malformed. |
| `upstream-projection-unavailable` | The source projection is unavailable for delivery. |
| `publication-policy-violation` | Publication governance policy denied delivery. |

Future reason codes require EIP governance approval. Existing reason codes must not be removed or repurposed after publication. New codes must be additive unless a future major delivery contract version explicitly defines a breaking migration.

## 13. Website Delivery Field Set

The Website-facing delivery representation may contain only these top-level field groups:

| Field group | Required | Owner | Purpose |
| --- | --- | --- | --- |
| `delivery_metadata` | Yes | EIP | Identifies delivery contract version, publication policy version, delivery generation context, and delivery status. |
| `projection_reference` | Yes | EIP | Identifies the source `ExecutiveIntelligenceProjection` and projection version context. |
| `publication` | Yes | EIP | Carries publication status and publication eligibility indicators. |
| `eligibility` | Yes | EIP | Carries deterministic Website rendering eligibility decisions. |
| `compatibility` | Yes | EIP | Carries platform-owned compatibility indicators. |
| `version_context` | Yes | EIP | Carries upstream contract and methodology version references. |
| `lineage` | Yes | EIP | Carries safe lineage references to projection, package, derived artifact, catalog entry, snapshot, and Assessment Service provenance. |
| `classification` | Yes | EIP | Carries field and response classification indicators approved for Website delivery. |
| `limitations` | Yes | EIP | Carries limitations that must remain visible in Website rendering. |
| `dashboard_content` | Conditional | EIP | Carries projection-approved Website-renderable content only when eligibility allows it. |
| `rendering_guidance` | Conditional | EIP | Carries projection-approved ordering, grouping, labels, and visibility instructions. |
| `failure` | Conditional | EIP | Carries stable fail-closed reason codes and safe non-authoritative status. |

No other top-level field group is allowed without approved EIP architecture and versioning review.

## 14. Lineage Fields

The delivery contract must preserve safe end-to-end lineage.

Required lineage concepts:

- delivery contract version
- delivery publication policy version
- `ExecutiveIntelligenceProjection` identity
- projection contract version
- projection rule version
- `ExecutiveIntelligencePackage` reference
- package contract version
- package assembly rule version
- derived artifact reference or references
- derivation rule version
- derivation runtime version
- catalog admission reference or references
- catalog admission policy version
- producer snapshot identity
- Snapshot Integration Contract or response contract version
- `BusinessDecisionPackage` contract version
- assessment version
- methodology version
- component version references when approved for delivery
- Assessment Service provenance reference
- production-authority status

Lineage fields must be references, safe identifiers, stable hashes, or approved metadata only. The delivery contract must not include raw snapshot bodies, raw package bodies, raw catalog entries, raw derived artifact internals, source evidence bodies, private file paths, credentials, or internal repository locations.

## 15. Version Fields

The delivery contract must include version fields sufficient for Website recognition and audit.

Required version concepts:

- delivery contract version
- delivery publication policy version
- projection contract version
- projection rule version
- package contract version
- package assembly rule version
- snapshot response contract version
- `BusinessDecisionPackage` contract version
- assessment version
- methodology version
- derivation rule version
- derivation runtime version
- component version references when approved for Website delivery

Version fields must be explicit. The Website must not infer any of these values.

## 16. Limitation Fields

Limitations are mandatory for governed Website delivery.

The delivery contract must include limitations for:

- projection limitations
- package limitations
- production-authority limitations
- assessment methodology limitations exposed through lineage
- compatibility limitations
- freshness or supersession limitations
- publication limitations
- classification and field visibility limitations
- dashboard rendering limitations

Limitations must be visible whenever governed content is rendered. If limitation visibility cannot be established, the delivery representation must fail closed with `limitations-not-visible`.

The Website must not hide, rewrite, summarize away, replace, reorder into invisibility, or convert limitations into marketing claims.

## 17. Eligibility Fields

The delivery contract must include eligibility fields that state whether the Website may render content as governed projection output.

Required eligibility fields:

- projection eligible for dashboard
- publication state
- compatibility state
- authorization scope state
- lineage state
- limitation visibility state
- freshness state
- classification state
- content source type
- failure reason codes when any eligibility field is non-passing

Eligibility fields are EIP-owned decisions. The Website may use them to choose deterministic UI states but must not recompute them.

## 18. Classification Fields

Every delivered field must carry or inherit a classification approved for Website delivery.

Allowed classification concepts:

- `public`
- `portal_operational`
- `client_confidential`
- `restricted_assessment`

Prohibited classification concepts:

- raw evidence
- credentials and secrets
- authentication and security internals
- control-plane internals
- unapproved personal data

Classification does not grant access. Authorization, publication status, eligibility, compatibility, lineage completeness, limitation visibility, and field allowlisting must also pass.

## 19. Compatibility Indicators

The delivery contract must expose compatibility indicators as platform-owned facts.

Required compatibility indicators:

- delivery contract compatibility
- projection contract compatibility
- package contract compatibility
- snapshot lineage compatibility
- methodology compatibility
- component version compatibility when exposed
- publication policy compatibility
- Website rendering eligibility compatibility

Compatibility indicators must have deterministic states and stable reason codes. The Website may consume the indicators but must not calculate them.

## 20. Prohibited Delivery Fields

The delivery contract must never include:

- raw `ExecutiveAssessmentSnapshot` bodies
- raw `BusinessDecisionPackage` bodies
- raw Executive Intelligence Package bodies
- raw catalog entries
- raw derived artifact internals
- raw evidence content
- source documents
- source file paths
- private repository URLs
- credentials, secrets, keys, tokens, passwords, factors, refresh tokens, or access tokens
- internal assessment methodology configuration
- answer-level scoring internals
- scoring weights
- hidden rationale
- analyst private notes unless separately approved and projected
- unapproved findings
- unapproved recommendations
- unredacted audit event bodies
- internal error payloads
- stack traces
- control-plane hostnames
- filesystem paths
- network routes
- service credentials
- authorization policy internals
- identity-provider claim bodies
- tenant membership records
- personal data not explicitly approved for delivery
- Website UI state as upstream truth
- synthetic demonstration values in governed projection delivery

Presence of a prohibited field is a contract violation and must fail closed.

## 21. Prohibited Website Assumptions

The Website must not assume:

- a route implies projection eligibility
- a successful fetch implies compatibility
- a known field name implies safe rendering
- authentication implies authorization
- cached content is current
- missing limitations mean no limitations exist
- missing lineage can be inferred from visible identifiers
- projection fields can be repaired or normalized client-side
- stale content can be rendered with a warning as authoritative
- synthetic demonstration content can stand in for governed projection content
- Website-controlled IDs replace EIP or Assessment Service lineage identifiers
- field order, layout, or labels are business truth
- unsupported contract versions are backward compatible by default

The Website must fail closed when these assumptions would be required to render content.

## 22. Producer Responsibilities

Within this architecture, EIP is the producer of the Website-facing delivery representation.

EIP must:

- publish only from approved `ExecutiveIntelligenceProjection` artifacts
- preserve projection immutability
- preserve package and snapshot lineage
- expose delivery contract version identity
- expose projection, package, snapshot, assessment, methodology, derivation, and publication version context
- determine compatibility before publication
- determine publication eligibility before delivery
- determine publication status
- determine freshness state
- include mandatory limitations
- include field classifications
- exclude prohibited fields
- provide stable fail-closed reason codes
- fail closed when eligibility, lineage, compatibility, classification, freshness, or limitation visibility is unclear

EIP must not:

- produce `ExecutiveAssessmentSnapshot` artifacts
- modify Assessment Service truth
- recompute assessment outputs
- mutate source projections or packages
- embed raw upstream artifacts in the Website delivery contract
- delegate compatibility decisions to the Website
- delegate eligibility decisions to the Website

## 23. Consumer Responsibilities

Within this architecture, the Website is the consumer of the delivery representation.

The Website must:

- recognize supported delivery contract versions
- render only allowlisted fields
- preserve and display required limitation indicators
- preserve lineage visibility at the approved level of detail
- use EIP-provided compatibility and eligibility indicators
- map stable fail-closed reason codes to deterministic UI states
- keep synthetic demonstration content separate from governed projection content
- fail closed when required delivery fields are missing, unsupported, ambiguous, stale, incompatible, unclassified, unpublished, unauthorized, or ineligible

The Website must not:

- validate snapshots
- inspect raw packages
- inspect derived artifacts
- inspect catalog entries
- create projections
- determine eligibility
- determine compatibility
- recompute assessment truth
- generate AI narratives from projection content
- implement dashboard behavior against any upstream artifact other than the approved delivery representation

## 24. Future API Boundary

This architecture defines the contract that a future API may publish. It does not define or authorize the API.

Any future API boundary must:

- publish the EIP-owned delivery representation only
- preserve delivery contract version identity
- preserve fail-closed reason codes
- preserve lineage, limitation, eligibility, freshness, classification, and compatibility indicators
- avoid exposing raw upstream artifacts
- avoid exposing control-plane internals
- avoid direct Website access to EIP storage or Assessment Service artifacts
- require separate approval for authentication, authorization, transport, persistence, logging, telemetry, and deployment

The Website must not integrate through direct platform storage, shared filesystems, message queues, protected control-plane services, credentials, or back-channel connectivity unless a future approved architecture explicitly defines that boundary.

## 25. Implementation Sequencing

No implementation is authorized by this document.

Recommended sequencing before Website implementation:

1. Approve this EIP-owned Website-facing Projection Delivery Contract and Versioning Policy Architecture.
2. Approve a bounded EIP implementation sprint for the delivery contract model only.
3. Implement delivery contract generation from existing `ExecutiveIntelligenceProjection` artifacts only.
4. Add EIP tests for versioning, eligibility, publication status, freshness, stable reason codes, prohibited fields, immutability, lineage preservation, and fail-closed behavior.
5. Perform EIP implementation review and architecture conformance review.
6. Approve a bounded Website implementation sprint for delivery contract consumption and fail-closed rendering only.
7. Add Website tests proving it does not validate snapshots, inspect raw packages, inspect derived artifacts, inspect catalog entries, create projections, determine eligibility, determine compatibility, recompute assessment truth, or mix synthetic demonstration content with governed projection content.
8. Perform Website accessibility, security, implementation, and architecture conformance review.

No Website implementation should begin before this document is approved and the EIP delivery contract implementation sprint is separately approved and completed.

## 26. Architecture Review

This architecture fills the remaining prerequisite between EIP-owned `ExecutiveIntelligenceProjection` output and Website-owned dashboard rendering.

It preserves the approved architecture stack:

```text
Assessment Service truth
  -> immutable ExecutiveAssessmentSnapshot
  -> EIP compatibility validation
  -> EIP catalog admission
  -> EIP derivation
  -> EIP package
  -> EIP projection
  -> EIP Website-facing delivery contract
  -> Website rendering
```

The delivery contract does not redefine projection behavior. It defines the governed publication representation that the Website may consume. It also prevents the Website from reaching back into snapshot, catalog, derivation, package, or projection internals.

No architectural drift was identified. The document adds a publication boundary that is consistent with the approved Website architecture and the EIP projection architecture.

## 27. Repository Ownership Review

Repository ownership remains intact.

The Assessment Service remains the exclusive owner of assessment truth, `ExecutiveAssessmentSnapshot`, methodology, `BusinessDecisionPackage`, and snapshot serialization.

The Executive Intelligence Platform remains the owner of projection production, publication, delivery contract versioning, eligibility decisions, compatibility decisions, and lineage-preserving delivery representations.

The Website remains the owner of rendering, visualization, layout, navigation, deterministic presentation, and fail-closed UI behavior.

No Assessment Service or Website responsibility is moved into this repository beyond the EIP-owned delivery contract and publication policy boundary.

## 28. Governance Review

This architecture conforms to repository governance by:

- preserving producer / consumer isolation
- preserving immutable evidence semantics
- keeping business truth externally owned by the Assessment Service
- keeping EIP as the owner of downstream projection publication decisions
- preventing Website-side validation, derivation, package assembly, projection creation, eligibility decisions, compatibility decisions, and assessment recomputation
- defining stable reason codes for deterministic downstream automation and audit
- denying unallowlisted or prohibited fields by default
- requiring fail-closed behavior for ambiguity, incompatibility, stale content, missing lineage, missing limitations, unsupported versions, and classification failures
- avoiding implementation, APIs, persistence, transport, infrastructure, deployment, UI, and technology decisions

The architecture is governance-first and implementation-ready only after explicit implementation approval.

## 29. Recommended Document Location

Recommended and implemented location:

```text
docs/architecture/website-facing-projection-delivery-contract-versioning-policy-architecture-v1.md
```

## 30. Recommended Commit Message

```text
arch: define website-facing projection delivery contract versioning policy
```

## 31. Recommended Git Tag

```text
website-facing-projection-delivery-contract-versioning-policy-architecture-v1
```
