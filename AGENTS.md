# Agent Governance

This file defines the standing operating rules for AI agents and automated contributors working in the Executive Intelligence Platform repository.

## Repository Identity

The Executive Intelligence Platform is a separate bounded context from the Nguyen AI Assessment Service.

The Assessment Service is permanently complete and remains the sole producer of immutable `ExecutiveAssessmentSnapshot` artifacts. This repository is a consumer-only bounded context.

Business truth originates exclusively from the Assessment Service. The Executive Intelligence Platform consumes immutable `ExecutiveAssessmentSnapshot` artifacts through the Snapshot Integration Contract and may derive intelligence from admitted snapshots only within the limits of repository governance.

## Non-Negotiable Boundary Rules

Agents must preserve the producer/consumer separation at all times.

Agents must not:

- implement Assessment Service behavior in this repository
- modify, reinterpret, recompute, or replace deterministic assessment truth
- create a competing assessment model, score, rubric, rank, grade, or source-of-truth assessment result
- make this repository a producer of `ExecutiveAssessmentSnapshot` artifacts
- introduce implementation before approval
- create Sprint 1 architecture unless explicitly instructed
- introduce runtime, APIs, persistence, AWS infrastructure, databases, or technology decisions unless explicitly approved

Agents may:

- maintain governance documentation
- clarify bounded context rules
- propose future architecture review materials when requested
- document constraints that protect the Snapshot Integration Contract
- identify risks, ambiguities, and missing approval gates

## Governance-First Engineering

All work in this repository must begin with governance and architectural intent before implementation. Agents must treat documentation as the control plane for repository behavior.

Before adding implementation, agents must verify that:

- the work is explicitly approved
- the relevant governance document permits the change
- the change does not weaken producer/consumer separation
- the change does not introduce hidden technology choices
- the change preserves immutable snapshot semantics

If these conditions are not met, agents must stop and ask for review.

## Architectural Review Workflow

Agents must use the repository governance document as the source of process truth. Proposed architecture must be documented before implementation and must distinguish clearly between:

- admitted facts
- constraints
- decisions
- open questions
- deferred decisions
- non-goals

Architectural review must happen before any code, runtime, service, persistence, or infrastructure work.

## Sprint Workflow

Agents must not invent sprint scope. Sprint work begins only after an approved sprint document exists.

Each sprint must identify:

- governance constraints
- architectural scope
- non-goals
- allowed files or areas of change
- acceptance criteria
- review requirements

If a requested task does not identify an approved sprint scope, agents must keep changes limited to governance or ask for clarification.

## Documentation Standards

Documentation must be precise, durable, and written for future maintainers.

Agents should:

- use plain language
- state boundaries explicitly
- avoid implementation assumptions
- record decisions separately from speculation
- keep deterministic assessment truth separate from derived intelligence
- link related governance documents

Agents should not:

- imply unapproved architecture
- name specific technologies before approval
- create placeholders that look like committed decisions
- use ambiguous phrases such as "source of truth" without naming the owning bounded context

## Commit Standards

Commits should be small, reviewable, and scoped to a single intent.

Commit messages should use clear conventional prefixes where practical, such as:

- `docs:`
- `chore:`
- `arch:`
- `governance:`

Implementation commits must not be mixed with governance-only changes unless explicitly approved.

## Release And Tagging Standards

Governance baselines may be tagged when approved. Tags should identify durable governance milestones and must not imply production runtime readiness unless implementation has separately been approved and released.

Suggested governance tag format:

- `governance-v1`
- `governance-v1.1`

Runtime or product release tags are out of scope until implementation governance permits them.

## Stop Conditions

Agents must stop and request review when:

- a task would introduce implementation
- a task would create Sprint 1 architecture without explicit instruction
- a task would define runtime, API, database, infrastructure, or technology choices prematurely
- a task would blur the Assessment Service and Executive Intelligence Platform boundary
- a task would change the meaning of immutable `ExecutiveAssessmentSnapshot` data
- a task would create or imply a new source of assessment truth

When stopped, agents should state the specific governance boundary involved and the approval needed to continue.
