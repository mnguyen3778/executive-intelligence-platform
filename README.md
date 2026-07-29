# Executive Intelligence Platform

The Executive Intelligence Platform is a governance-first repository for a separate bounded context that consumes immutable executive assessment artifacts and derives executive intelligence from them.

This repository is intentionally distinct from the Nguyen AI Assessment Service.

## Repository Vision

The platform exists to provide an executive intelligence layer over completed assessment outputs. Its purpose is to support interpretation, synthesis, reporting, decision support, and future executive-facing workflows without becoming a source of assessment truth.

Business truth originates exclusively from the Nguyen AI Assessment Service.

The Assessment Service is permanently considered complete and is the sole producer of immutable `ExecutiveAssessmentSnapshot` artifacts. The Executive Intelligence Platform is a consumer-only bounded context.

## Source Of Truth

The platform consumes immutable `ExecutiveAssessmentSnapshot` artifacts through the Snapshot Integration Contract.

The platform may derive intelligence from admitted snapshots, but it must never:

- alter deterministic assessment truth
- reinterpret deterministic assessment truth
- recompute deterministic assessment truth
- replace deterministic assessment truth
- create competing assessment outputs
- act as a producer of `ExecutiveAssessmentSnapshot` artifacts

Any derived intelligence must remain traceable to admitted immutable snapshots and must be clearly distinguished from assessment truth.

## Governance Baseline

Permanent repository governance is defined in:

- [AGENTS.md](./AGENTS.md)
- [docs/governance/repository-governance-v1.md](./docs/governance/repository-governance-v1.md)

These documents define repository ownership, bounded context rules, architectural review workflow, sprint workflow, documentation standards, commit standards, release standards, implementation approval, and future evolution philosophy.

## Current Scope

This repository currently contains only the permanent governance baseline.

The following are intentionally not defined yet:

- Sprint 1 architecture
- implementation
- runtime
- APIs
- persistence
- AWS infrastructure
- databases
- technology decisions

No implementation work may begin until explicitly approved through the governance process.
