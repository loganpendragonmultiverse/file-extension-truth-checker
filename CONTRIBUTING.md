# Contributing

Bug reports, focused signature additions, documentation improvements, and pull requests are welcome. Please open an issue before adding a broad or ambiguous file family.

For code changes:

1. Fork the repository and create a focused branch.
2. Install with `python -m pip install -e . pytest build`.
3. Add a small, non-copyrighted fixture or synthetic byte sequence for every signature change.
4. Run `python -m pytest` and `python -m build`.
5. Update the recognized-families list, limitations, and changelog when behavior changes.
6. Submit a pull request explaining false-positive risk and verification performed.

Detection must stay conservative and read-only. A maintainer reviews every pull request; passing checks do not guarantee merge.
