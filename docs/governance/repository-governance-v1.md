# Repository Governance v1

## Status

This document establishes the permanent governance baseline for the Executive Intelligence Platform repository.

It is governance-only. It does not define Sprint 1 architecture, implementation, runtime, APIs, persistence, AWS infrastructure, databases, or technology decisions.

## Repository Vision

The Executive Intelligence Platform exists to provide an executive intelligence layer over completed assessment outputs. It is responsible for consuming immutable assessment snapshots and enabling future intelligence, synthesis, reporting, and executive-facing workflows derived from those admitted artifacts.

The platform must remain analytically useful without becoming a source of deterministic assessment truth.

## Architectural Philosophy

Architecture in this repository must be deliberate, documented, and reviewable before implementation.

The repository favors:

- explicit bounded contexts
- immutable inputs
- traceable derived intelligence
- separation between facts and interpretation
- conservative evolution
- clear approval gates
- durable documentation before code

The repository rejects premature implementation and technology-led design. Technical decisions must follow approved architectural intent, not precede it.

## Governance-First Engineering

Governance is the first engineering artifact in this repository. It defines what future work may and may not do.

Every future change must be evaluated against:

- bounded context ownership
- producer/consumer separation
- immutability of admitted snapshots
- preservation of deterministic assessment truth
- explicit approval status
- documentation quality
- architectural reversibility where decisions remain unsettled

Implementation may begin only after governance permits it and an approved architecture or sprint scope identifies the allowed work.

## Repository Ownership

This repository owns the Executive Intelligence Platform bounded context only.

It does not own:

- the Nguyen AI Assessment Service
- assessment production workflows
- deterministic assessment scoring
- assessment rubrics
- canonical assessment interpretation
- generation of `ExecutiveAssessmentSnapshot` artifacts
- mutation of admitted assessment snapshots

It may own future platform capabilities that consume admitted immutable snapshots and produce clearly labeled derived intelligence, subject to approved architecture.

## Producer And Consumer Separation

The Nguyen AI Assessment Service is permanently considered complete and is the sole producer of immutable `ExecutiveAssessmentSnapshot` artifacts.

The Executive Intelligence Platform is a consumer-only bounded context.

Business truth originates exclusively from the Assessment Service. The platform consumes `ExecutiveAssessmentSnapshot` artifacts through the Snapshot Integration Contract.

The Executive Intelligence Platform must not:

- produce `ExecutiveAssessmentSnapshot` artifacts
- alter admitted snapshots
- reinterpret deterministic assessment truth
- recompute deterministic assessment outcomes
- replace Assessment Service facts with platform-derived values
- create a parallel assessment source of truth
- treat derived intelligence as canonical assessment truth

The platform may:

- admit snapshots through the Snapshot Integration Contract once that contract is approved
- validate conformance to the approved contract
- derive intelligence from admitted immutable snapshots
- preserve traceability between derived intelligence and source snapshots
- present derived intelligence as separate from deterministic assessment truth

## Bounded Context Rules

The Assessment Service bounded context owns assessment truth.

The Executive Intelligence Platform bounded context owns downstream intelligence derived from admitted snapshots.

The boundary must remain explicit in naming, documentation, data models, architecture, and future implementation.

Rules:

- Deterministic assessment fields are externally owned.
- Snapshot artifacts are immutable once admitted.
- Derived intelligence must be labeled as derived.
- Any derived output must be traceable to its source snapshot or snapshots.
- No platform component may claim authority over assessment correctness.
- No platform workflow may modify source assessment data to fit downstream needs.
- Ambiguity in source data must be surfaced as an intake, contract, or governance issue rather than silently corrected.

## Snapshot Integration Contract

The Snapshot Integration Contract is the future boundary through which the platform consumes immutable `ExecutiveAssessmentSnapshot` artifacts.

This governance baseline does not define the contract schema, transport, storage mechanism, validation technology, or runtime behavior. Those decisions are intentionally deferred until an approved architecture phase.

The contract must preserve these principles when later defined:

- Assessment Service remains the sole producer.
- Snapshot artifacts remain immutable.
- The platform consumes snapshots without changing deterministic assessment truth.
- Derived intelligence remains separate from assessment truth.
- Contract failures are handled as integration issues, not as authorization to reinterpret source data.

## Architectural Review Workflow

Architecture must be reviewed before implementation.

An architecture proposal must include:

- problem statement
- scope
- non-goals
- bounded context impact
- Snapshot Integration Contract impact
- admitted facts
- assumptions
- proposed decisions
- deferred decisions
- risks
- alternatives considered
- review status

Architecture documents must distinguish clearly between approved decisions and exploratory ideas.

No architecture proposal may authorize implementation until it has been explicitly approved through repository governance.

## Sprint Workflow

Sprint work must be created from approved governance and architecture.

Each sprint document must define:

- objective
- scope
- non-goals
- governance constraints
- architectural dependencies
- allowed implementation areas
- documentation requirements
- acceptance criteria
- review and approval requirements

Sprint 1 architecture has not been created by this baseline and must not be inferred from it.

No agent or contributor may invent sprint scope from repository vision alone.

## Documentation Standards

Documentation is a governed artifact.

Repository documentation must:

- use clear, durable language
- identify the owning bounded context
- distinguish facts, decisions, assumptions, and open questions
- avoid unapproved technology commitments
- avoid hidden implementation design
- preserve Assessment Service authority over business truth
- preserve Executive Intelligence Platform consumer-only status

Documentation should be updated in the same change as any approved governance or architecture decision it affects.

## Commit Standards

Commits must be scoped, reviewable, and explain intent.

Use concise commit messages. Conventional prefixes are encouraged:

- `docs:` for documentation
- `governance:` for governance baseline or policy changes
- `arch:` for approved architecture artifacts
- `chore:` for repository maintenance

Do not mix unrelated governance, architecture, and implementation changes in a single commit unless explicitly approved.

Implementation commits are not allowed until implementation has been approved.

## Release And Tagging Standards

Repository tags should communicate the maturity of the artifact being tagged.

Governance releases may use:

- `governance-v1`
- `governance-v1.1`
- `governance-v2`

Architecture releases may use a future naming standard once architecture governance is approved.

Product, runtime, or deployment release tags are out of scope until implementation governance permits them.

Tags must not imply production readiness unless the repository actually contains approved, reviewed, and releasable implementation.

## Implementation Approval Workflow

Implementation requires explicit approval.

Before implementation begins, the repository must have:

- approved governance permitting the category of work
- approved architecture defining the intended design
- approved sprint scope identifying the work to be performed
- documented non-goals
- documented acceptance criteria
- documented review requirements

Without these artifacts, contributors and agents must stop before writing implementation.

Implementation approval must be specific. Broad repository vision is not implementation approval.

## Architectural Principles

Future architecture must follow these principles:

- Preserve the Assessment Service as the exclusive source of business truth.
- Preserve immutable `ExecutiveAssessmentSnapshot` semantics.
- Keep producer and consumer responsibilities separate.
- Make derived intelligence traceable to admitted snapshots.
- Prefer explicit contracts over implicit coupling.
- Document decisions before implementation.
- Defer technology choices until the problem and boundary are approved.
- Avoid irreversible decisions before they are necessary.
- Treat ambiguity as a governance or contract issue.
- Keep the Executive Intelligence Platform independently evolvable within its bounded context.

## Future Repository Evolution Philosophy

This repository should evolve in controlled layers:

1. Governance baseline.
2. Architecture proposals.
3. Approved sprint definitions.
4. Implementation within approved scope.
5. Verification and review.
6. Release and tagging.

Each layer should preserve the integrity of the previous layer. Future evolution should expand capability without eroding the bounded context boundary or transforming derived intelligence into assessment truth.

The platform may become richer over time, but it must remain a consumer of immutable assessment snapshots and never become the Assessment Service by accretion.

## Current Explicit Non-Goals

This baseline does not create or authorize:

- Sprint 1 architecture
- source code implementation
- runtime behavior
- APIs
- persistence
- AWS infrastructure
- databases
- technology decisions
- deployment model
- operational model
- Snapshot Integration Contract schema

These topics require future explicit review and approval.
