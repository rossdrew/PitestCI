# Pitest Badge

A [Pitest](https://pitest.org) mutation score badge for your README, hosted in your own repository. No account, service or secret: one step after Pitest in your GitHub Actions workflow.

![mutation coverage: 75%](https://img.shields.io/badge/mutation%20coverage-75%25-yellow)

## Usage

Run Pitest with XML output (`outputFormats = listOf("XML", "HTML")` in Gradle, `<outputFormats>XML,HTML</outputFormats>` in Maven), then:

```yaml
on:
  push:
    branches: [main]
  pull_request:

permissions:
  contents: write   # to push the badge

jobs:
  mutation:
    runs-on: ubuntu-latest
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

### The HTML report too

```yaml
      - uses: rossdrew/PitestCI@v1
        with:
          report: true
```

pushes Pitest's HTML report to `gh-pages` under `pitest/` (plus a copy of the badge at its root). Set Pages to **Deploy from a branch**, `gh-pages`, once in the repository's settings; the report is then at `https://<owner>.github.io/<repo>/pitest/`. Anything else in `gh-pages` is kept, but like `badges` the branch keeps only its latest commit.

## Inputs

| Input | Default | |
|---|---|---|
| `reports` | every `mutations.xml` in the workspace | Glob(s), space-separated. Several reports (modules) are added together. |
| `label` | `mutation coverage` | The badge's left-hand text. |
| `thresholds` | `60,80` | Red below the first, yellow below the second, green above. |
| `publish` | on a push to the default branch | `true`/`false` to override. |
| `badge-branch` | `badges` | Keeps only its latest commit; other files in it are kept. |
| `badge-file` | `pitest.json` | Its path in that branch; use different ones for several badges. |
| `report` | `false` | Also publish the HTML report. |
| `pages-branch` | `gh-pages` | Where the report goes. |
| `pages-path` | `pitest` | The report's folder; one subfolder per module when there are several. |
| `output-dir` | `pitest-badge` | The badge JSON is also written here, e.g. to upload as an artifact. |
| `token` | `github.token` | Needs contents write. |

Outputs: `score`, `detected`, `total`, `color`, `badge-file`, `badge-url`.

The score is the share of mutants Pitest marks detected (killed, timed out, crashing the JVM, …), the same figure as its own report.

## Notes

- Public repositories only for the badge: shields.io can't read files from a private one.
- Maven with `timestampedReports` on leaves older reports around; turn it off or point `reports` at the latest.
- Needs Python 3 on the runner (all GitHub-hosted runners have it).

## License

[MIT](LICENSE)
