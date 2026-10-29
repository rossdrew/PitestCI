# Pitest Badge

[![Test](https://github.com/rossdrew/PitestCI/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/rossdrew/PitestCI/actions/workflows/test.yml)

A [Pitest](https://pitest.org) mutation score badge for your README, hosted in your own repository. No account, service or secret: one step after Pitest in your GitHub Actions workflow.

[![self-test](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/rossdrew/PitestCI/self-test-badges/pitest.json)](https://github.com/rossdrew/PitestCI/tree/self-test-badges)

That one is live: this repository's own tests publish it from a deliberately half-tested [sample](tests/projects) on every push to `main`.

- Gradle or Maven, single or multi-module: it reads Pitest's `mutations.xml`.
- The score in every run's job summary, with a table per package, pull requests included.
- Optionally Pitest's HTML report on GitHub Pages.

## Usage

Run Pitest with XML output (`outputFormats = listOf("XML", "HTML")` in Gradle, `<outputFormats>XML,HTML</outputFormats>` in Maven), then add the step:

```yaml
on:
  push:
    branches: [main]
  pull_request:

jobs:
  mutation:
    runs-on: ubuntu-latest
    permissions:
      contents: write   # to push the badge
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: 21
      - run: ./gradlew pitest          # or: mvn test-compile org.pitest:pitest-maven:mutationCoverage
      - uses: rossdrew/PitestCI@v1
```

On pushes to your default branch it commits the badge to a `badges` branch; on pull requests it only writes the score to the job summary. Then add to your README (`<owner>/<repo>` being yours):

```markdown
[![Mutation coverage](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/<owner>/<repo>/badges/pitest.json)](https://github.com/<owner>/<repo>/actions)
```

The `badge-url` output gives the exact URL.

### Keeping the write token away from your build

Above, the token that can push to your repository is in the same job as your build and every plugin and dependency it runs. To keep them apart, run Pitest without it and publish from a job that only downloads the report (the Action needs no checkout):

```yaml
jobs:
  mutation:
    runs-on: ubuntu-latest
    steps:
      # ... checkout, Java, ./gradlew pitest as above
      - uses: actions/upload-artifact@v4
        with:
          name: pitest
          path: build/reports/pitest

  badge:
    if: github.event_name == 'push'
    needs: mutation
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: pitest
      - uses: rossdrew/PitestCI@v1
```

### The HTML report too

With `report: true` it also puts Pitest's HTML report, under `pitest/`, and a copy of the badge into a GitHub Pages site and uploads it; a job of yours deploys it. Set Pages' source to **GitHub Actions** once in the repository's settings; the report is then at `https://<owner>.github.io/<repo>/pitest/`.

```yaml
  badge:
    # ... as above
    steps:
      # ...
      - uses: rossdrew/PitestCI@v1
        with:
          report: true

  pages:
    needs: badge
    runs-on: ubuntu-latest
    permissions:
      pages: write
      id-token: write
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - id: deployment
        uses: actions/deploy-pages@v4
```

(The Action can't deploy for you: deploying needs the `github-pages` environment, which only a job can set. Pushing the report to a `gh-pages` branch instead doesn't work either: GitHub doesn't rebuild Pages for pushes made with the workflow's token.)

## Inputs

| Input | Default | |
|---|---|---|
| `reports` | every `mutations.xml` in the workspace | Glob(s), space-separated. Several reports (modules) are added together. |
| `label` | `mutation coverage` | The badge's left-hand text. |
| `thresholds` | `60,80` | Red below the first, yellow below the second, green above. |
| `publish` | on a push to the default branch | `true`/`false` to override. |
| `badge-branch` | `badges` | Keeps only its latest commit; other files in it are kept. |
| `badge-file` | `pitest.json` | Its path in that branch; use different ones for several badges. |
| `report` | `false` | Also build a Pages site with the HTML report and, when publishing, upload it for `actions/deploy-pages`. |
| `pages-path` | `pitest` | The report's folder in the site; one subfolder per module when there are several. |
| `site-dir` | `pitest-site` | Where the site is assembled. |
| `output-dir` | `pitest-badge` | The badge JSON is also written here, e.g. to upload as an artifact. |
| `token` | `github.token` | Needs contents write. |

Outputs: `score`, `detected`, `total`, `color`, `badge-file`, `badge-url`, `site-dir`.

The score is the share of mutants Pitest marks detected (killed, timed out, crashing the JVM, …), the same figure as its own report.

## Versions

`@v1` follows the latest 1.x release; pin `@v1.0.0` (or a commit) to stay put. See the [changelog](CHANGELOG.md).

## Notes

- Public repositories only for the badge: shields.io can't read files from a private one.
- Maven with `timestampedReports` on leaves older reports around; turn it off or point `reports` at the latest.
- Needs Python 3 on the runner (all GitHub-hosted runners have it).

## License

[MIT](LICENSE)
