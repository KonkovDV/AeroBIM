## Summary

- what changed:
- why it changed:
- risk notes:

## Validation

- [ ] `python -m ruff format --check src tests`
- [ ] `python -m ruff check src tests`
- [ ] `python -m mypy src`
- [ ] `pytest tests -q`
- [ ] docs updated if behavior/contracts/governance changed

## Agent bus

- [ ] Claim comment uses `aerobim.agent_bus.v1` before this branch
- [ ] One open PR for that issue
- [ ] `check-thread` names one holder; `check-run` gets the Actions jobs API payload
- [ ] The diff does not write `summary.passed` or set `customer_go`

## Additional Checks

- [ ] No secrets or private data in diff
- [ ] API/report contract changes are documented
- [ ] Benchmark or quality claims reference concrete artifacts
