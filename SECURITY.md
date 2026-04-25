# Security Policy

## Scope

AeroBIM is maintained as an open-source engineering and research repository.

Security support is best effort for the active default branch and latest release line. Experimental snapshots and local forks are not guaranteed to receive fixes.

## Supported Surface

| Surface | Support |
| --- | --- |
| default branch (`main`) | best effort |
| latest release tag | supported for coordinated fixes |
| historical snapshots, local forks, generated artifacts | unsupported |

## Reporting a Vulnerability

Do not disclose exploitable details in public issues or pull requests.

Preferred channel:

1. GitHub private vulnerability reporting: https://github.com/KonkovDV/AeroBIM/security/advisories/new
2. If private reporting is temporarily unavailable, contact maintainers privately and delay public disclosure.

When reporting, include:

- affected component/path;
- minimal safe reproduction;
- impact scope;
- whether secrets or sensitive project data may be exposed.

## Response Targets

- acknowledgement within 5 business days;
- triage update within 14 calendar days;
- coordinated disclosure after fix or mitigation is available.

## In-Scope Areas

- CI/CD and workflow supply chain
- authentication and API boundary handling
- report export and persistence surfaces
- object storage adapters and optional Postgres index integration
- dependency and package security in backend/frontend pipelines

## Out of Scope

- vulnerabilities only present in downstream private forks
- social engineering and phishing not tied to this codebase
- incidents requiring access to third-party systems outside repository control

## Recommended Repository Controls

- private vulnerability reporting enabled
- secret scanning and push protection enabled
- code scanning (CodeQL or equivalent) enabled
- protected default branch with pull-request review gates
