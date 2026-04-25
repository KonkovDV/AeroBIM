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

## Additional Checks

- [ ] No secrets or private data in diff
- [ ] API/report contract changes are documented
- [ ] Benchmark or quality claims reference concrete artifacts
