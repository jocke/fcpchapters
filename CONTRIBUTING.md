# Development and tests

The executable is Ruby. Python tests use standard-library SQLite and plist support to mutate temporary fixture copies and run the Ruby CLI. Original fixture files must remain unchanged.

From the repository root, run the self-contained Ruby tests:

```sh
ruby tests/test_fcpchapters.rb
```

Install `minitest` if your Ruby installation does not include it. Integration cases explicitly skip when their private fixture is absent.

The integration suites depend on three specific development snapshots, not arbitrary libraries. They are intentionally not published:

```sh
FCPCHAPTERS_TEST_LIBRARY="/path/to/original/Sample Library.fcpbundle" ruby tests/test_fcpchapters.rb
python3 tests/test_timelines.py "/path/to/original/Sample Library.fcpbundle"
python3 tests/test_multiclip.py "/path/to/updated/Sample Library.fcpbundle"
python3 tests/test_effects.py "/path/to/effects/Sample Library.fcpbundle"
python3 tests/test_generators.py "/path/to/effects/Sample Library.fcpbundle"
python3 tests/test_events.py "/path/to/effects/Sample Library.fcpbundle"
python3 tests/test_diagnostics.py "/path/to/effects/Sample Library.fcpbundle"
FCPCHAPTERS_DIAGNOSTICS="/path/to/timing-diagnostics.json" ruby tests/test_diagnostic_replay.rb
```

The replay test requires a compatible anonymized diagnostic snapshot and skips when the environment variable is absent. Fixture-dependent tests use neutral Event, Project and clip names and fixed row IDs. They require matching anonymized snapshots; renaming arbitrary libraries does not make them suitable fixtures. Sanitized, redistributable fixtures are future work; passing only self-contained tests does not establish full integration coverage.

For bug reports, include the script version and exact error. Diagnostic exports contain project and clip names and internal metadata: review and redact them before sharing publicly. Do not attach whole libraries or media to issues by default.

The intended GitHub repository name is `fcpchapters`; the project uses the MIT License. Before publishing, select the repository owner. Push only this project directory, not its enclosing workspace, which contains private development material.
