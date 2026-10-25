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

This repository contains approved consumer-side snapshot admission, derivation,
projection, and delivery work. The Assessment Service remains the sole producer
of governed assessment conclusions. Further implementation still requires
explicit approval through the governance process.

## Local Phase 1G dependency setup

Use Python `>=3.14,<3.15` with the Assessment Service checkout beside this
repository, as `../nguyen-ai-assessment-service`. Its Python distribution is
`nguyen-ai-assessment-service==0.1.0`; the import package is named `assessment`.
EIP's verified admission imports `assessment.producer_snapshot_attestation`.
The producer distribution supplies the pinned `cryptography==50.0.2` runtime
dependency. EIP currently has no separate development requirements file or
installable distribution; its own source is selected with `PYTHONPATH=src`.

From the EIP repository root, create a fresh environment outside both
repositories and run:

```bash
env_root=$(mktemp -d "${TMPDIR:-/tmp}/eip-phase1g.XXXXXX")
python3.14 -m venv "$env_root/venv"
. "$env_root/venv/bin/activate"
python -m pip install -e ../nguyen-ai-assessment-service
python -c 'import assessment.producer_snapshot_attestation; import importlib.metadata as m; assert m.version("nguyen-ai-assessment-service") == "0.1.0"'
PYTHONPATH=src python -c 'import executive_intelligence_platform.projection_delivery.verified_admission'
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m unittest discover -s tests/projection_delivery -p test_verified_admission.py -q
```

The editable install reads a mutable local producer checkout. The existing EIP
cross-repository tests also insert the sibling producer source path themselves;
their passing result alone does not establish an installed dependency. A local
wheel built from the current candidate is likewise not an immutable release.
Phase 1G promotion must first commit the producer attestation and packaging
metadata at an identifiable revision, then commit EIP's reproducible setup.
These local instructions do not establish production dependency packaging,
signing-key custody, or deployment readiness.
