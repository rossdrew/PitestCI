# Changelog

## 1.1.1

No change to what the Action does.

- The README, which is also the Marketplace page, shows what you get (live badges, an example job summary, the report), compares Pitest Badge with the alternatives, and leads with the two-line setup.
- The description mentions the report too.
- Issue templates for bugs and feature requests.

## 1.1.0

Fixed:

- `report: true` pushed the HTML report to `gh-pages`, but GitHub doesn't rebuild Pages for pushes made with the workflow's token, so the site never updated. The Action now assembles the site (report under `pitest/`, badge at the root) and uploads it for `actions/deploy-pages`; set Pages' source to **GitHub Actions** and add a deploy job (see the README). The `pages-branch` input is gone; `site-dir` and the `site-dir` output are new.

Docs: how to keep the token that can push away from the build, by publishing from a job of its own.

## 1.0.0

First release as a GitHub Action (the 2017 PythonAnywhere script it replaces is in the history).

- Scores Pitest's `mutations.xml` (all modules added together): mutants detected over all mutants.
- Writes a shields.io endpoint badge, a job summary with a table per package, and the outputs `score`, `detected`, `total`, `color`, `badge-file` and `badge-url`.
- On a push to the default branch, commits the badge to a `badges` branch (a single commit; other files kept).
- `report: true` also publishes Pitest's HTML report to `gh-pages`.
