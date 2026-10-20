# Testing

```bash
python -m pip install -e . pytest build
python -m pytest
python -m build
```

Synthetic tests cover supported signatures and aliases, truncated audio framing,
ZIP subtypes, bounded EPUB reads, encrypted or unavailable identifying entries,
unreadable discovery, dangling collision targets and exclusive report creation.
No inspected source is renamed or modified. Exercise text, JSON and CSV CLI
reports and both normal and `--fail-on-mismatch` exit codes.

Install each wheel and source distribution into a fresh environment outside the
checkout, then run the full tests with `python -m pytest /path/to/tests` and verify
that imports resolve to that environment's site-packages. A synthetic mismatch
must propose a new name while preserving both source bytes and any destination.
The complete supported operating-system CI matrix must pass; Linux-only tests do
not constitute manual Windows or macOS acceptance.
