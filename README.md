# fcpchapters

Extract chapter markers from Final Cut Pro libraries as YouTube chapter timestamps, without exporting FCPXML. Version **0.5.17 — beta**.

## Requirements

- macOS with Ruby (tested during development with Ruby 3.4.9).
- macOS `sqlite3`, `plutil` and `pgrep`; SQLite must support JSON output.
- Ruby's `rexml` library for retiming inspection. If unavailable, install it with `gem install rexml`.

Python is needed only for some development tests, not to run fcpchapters.

## Usage

Close Final Cut Pro, then run:

```sh
ruby ./fcpchapters "/path/to/Library.fcpbundle"
```

A single Project is selected automatically. For multiple Projects, enter a number, or press Enter (or type A) to process all Projects in that Library.

```sh
ruby ./fcpchapters "/path/to/Library.fcpbundle" --all
ruby ./fcpchapters "/path/to/Library.fcpbundle" --project "Project name" --plain > chapters.txt
```

| Option | Purpose |
| --- | --- |
| `--all` | Process all Projects |
| `--project NAME` | Select a uniquely named Project |
| `--list-projects` | List available Projects |
| `--plain` | Write chapter text to stdout; status goes to stderr |
| `--json` | Write structured results with exact rational timestamps |
| `--diagnostics` | Export metadata and timing errors as JSON |
| `--version`, `--help` | Show version or usage |

Multiple Projects in plain mode receive separate headings. An unsuccessful Project does not stop the others; any processing failure gives exit status 1. JSON returns a single result for one successful selection, otherwise a `timelines`/`errors` object. Diagnostics have a separate `projects` schema.

## Chapter behavior

Markers outside a clip's visible trim are excluded. Times are calculated as rational seconds and rounded down to whole seconds for output. An Intro at 00:00 is added only when there is no existing zero timestamp and at least two distinct other timestamps. Short chapters, duplicate timestamps and insufficient chapter counts generate warnings.

Projects without chapter markers produce no chapter text or Intro. Confirmed empty Projects are reported as empty. Timing calculations are skipped when no reachable chapter markers exist; diagnostic mode retains full timing checks. In JSON, `timing_skipped` identifies unexamined timing counts, and empty Projects have `empty_project: true` and a null frame rate.

## Compatibility and read-only behavior

This is an experimental reader of Final Cut Pro's internal format, not an Apple-supported interface. It handles observed sequential clip layouts, trims, generators, forward retiming and centered transitions. Some behavior carries Beta verification notices. Reverse/freeze retiming, connected chapters, compound clips and other unrecognized layouts can still fail. Check extracted timestamps in Final Cut Pro before relying on unfamiliar layouts.

Catalog versions are checked by structure rather than restricted to a version whitelist. No oldest supported Final Cut version is claimed. Positive rational frame rates are accepted; broad frame-rate tests use synthetic fixtures.

The tool reads source metadata, copies databases to a temporary directory, queries those copies read-only and checks source hashes. It refuses open Final Cut Pro sessions and database sidecars. It does not modify or upgrade libraries. Keep Final Cut closed throughout processing.

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for tests and fixture requirements. Library bundles, media, diagnostic exports and personal chapter outputs are not distributed with this project.

## License

Licensed under the [MIT License](LICENSE). Copyright (c) 2026 Jocke Selin.
