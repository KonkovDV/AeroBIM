# Contributing to AeroBIM

Thank you for improving AeroBIM.

AeroBIM is an open-source platform for cross-modal BIM validation. Contributions should preserve deterministic behavior, explicit provenance, and clean architecture boundaries.

## Read First

1. [README.md](../README.md)
2. [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
3. [docs/TIER0_INDEX.md](../docs/TIER0_INDEX.md) · [docs/README.md](../docs/README.md)
4. [docs/architecture/TARGET_HYBRID_ARCHITECTURE_TZ_2026.md](../docs/architecture/TARGET_HYBRID_ARCHITECTURE_TZ_2026.md)
5. [docs/pilot-claim-boundary-2026.md](../docs/pilot-claim-boundary-2026.md)
6. [SECURITY.md](SECURITY.md) · [audit/reports/CLAIMS_LOCK_2026_07_17.md](../audit/reports/CLAIMS_LOCK_2026_07_17.md)

## Contribution Principles

- Keep dependency direction strict: core -> domain -> application -> infrastructure -> presentation.
- Do not bypass domain ports by wiring external libraries directly inside use cases.
- Preserve deterministic behavior in validation flows where deterministic mode already exists.
- Treat auditability as a feature: new behavior should be explainable in report artifacts.
- Keep diffs focused and reviewable.
- Do not claim customer accuracy, CDE-ready BCF, MEP system clash, or calculation *correctness* without evidence cited in [`audit/reports/CLAIMS_LOCK_2026_07_17.md`](../audit/reports/CLAIMS_LOCK_2026_07_17.md).

## Maintenance

Public GitHub may show a single contributor on origin. Dual-rater labeling (RT-001) is a customer-corpus protocol, not a git headcount. Do not silently upgrade Checkpoint `GO` or `customer_go`.

## Local Setup

Canonical clone recipe: [README Try it](../README.md#try-it). Windows Explorer: `run-jury.bat` at the clone root. If PowerShell blocks `Activate.ps1`, skip activation:

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev,raster]"
```

Linux/macOS:

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,raster]"
```

Optional local hooks (human `Co-authored-by:` kept; other identity trailers stripped):

```bash
git config core.hooksPath .githooks
```

Optional extras:

```bash
pip install -e ".[clash]"
pip install -e ".[enterprise]"
```

## Validation Baseline

Run before opening a pull request:

```bash
cd backend
python -m ruff format --check src tests
python -m ruff check src tests
python -m mypy src
pytest tests -q
```

Install extras `.[dev,raster]`: **0 failed** on a clean clone. Tests that need `pdf-agpl` or unpublished CI secrets skip. The publishable pin is `docs/evidence/runtime-baseline-latest.json` (`attested_by=ci`), not a local count.

If formatting fails:

```bash
python -m ruff format src tests
```

## Agent bus

Parallel sessions coordinate on issues, not in a second status channel. The protocol, claim comment, and CI rule are in [the agent bus](../docs/GH_AGENT_BUS.md). Check a comment or a run payload with `python -m aerobim.tools.agent_bus`.

## Git commits

Keep authorship truthful. If a **human** co-author materially contributed, use an explicit `Co-authored-by:` trailer. The commit-msg hook drops other identity trailers. Do not strip human provenance.

## Pull Request Checklist

1. Describe the problem and the decision, not only the code diff.
2. Include executed validation commands and outcomes.
3. Update docs when behavior, API, contracts, or operational guidance changes.
4. Add or update tests for bug fixes and new capability.
5. Do not commit secrets, private models, customer data, or local environment files.

## API and Contract Changes

For public API or report-contract changes:

- keep backward-compatibility intent explicit;
- document OpenAPI via the live `/openapi.json` endpoint (do not commit generated OpenAPI dumps);
- highlight migration impact in the PR description.

## License

By contributing, you agree that your contributions are provided under the MIT License.
