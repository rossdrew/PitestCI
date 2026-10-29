# Changelog

## 1.0.0

First release as a GitHub Action (the 2017 PythonAnywhere script it replaces is in the history).

- Scores Pitest's `mutations.xml` (all modules added together): mutants detected over all mutants.
- Writes a shields.io endpoint badge, a job summary with a table per package, and the outputs `score`, `detected`, `total`, `color`, `badge-file` and `badge-url`.
- On a push to the default branch, commits the badge to a `badges` branch (a single commit; other files kept).
- `report: true` also publishes Pitest's HTML report to `gh-pages`.
