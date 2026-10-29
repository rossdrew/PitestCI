"""Pitest mutation score badge: reads Pitest's mutations.xml, writes a shields.io endpoint badge,
summarises the score in the job summary and publishes the badge (and optionally the HTML report)
to branches of the repository.

Standard library only, so the Action needs no setup step. Inputs arrive as INPUT_* environment
variables set by action.yml.
"""

import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

SKIP_DIRS = {".git", "node_modules", ".gradle"}
BOT = ("github-actions[bot]", "41898282+github-actions[bot]@users.noreply.github.com")


@dataclass
class Score:
    detected: int = 0
    total: int = 0
    packages: dict = field(default_factory=lambda: defaultdict(lambda: [0, 0]))

    @property
    def percent(self):
        return round(100 * self.detected / self.total) if self.total else 0


def find_reports(patterns, root="."):
    """mutations.xml files matching the glob patterns, or every one under root when none are given."""
    if patterns:
        found = {p for pattern in patterns for p in glob.glob(pattern, root_dir=root, recursive=True)}
        return sorted(Path(root, p) for p in found)
    found = []
    for directory, subdirs, files in os.walk(root):
        subdirs[:] = sorted(d for d in subdirs if d not in SKIP_DIRS)
        if "mutations.xml" in files:
            found.append(Path(directory, "mutations.xml"))
    return found


def score(reports):
    """Adds up mutants over all reports (one per module); Pitest marks each one detected or not."""
    s = Score()
    for report in reports:
        for mutation in ET.parse(report).getroot().iter("mutation"):
            detected = mutation.get("detected") == "true"
            cls = mutation.findtext("mutatedClass", "")
            package = s.packages[cls.rpartition(".")[0] or "(default)"]
            package[0] += detected
            package[1] += 1
            s.detected += detected
            s.total += 1
    return s


def colour(percent, thresholds):
    low, high = thresholds
    return "brightgreen" if percent >= high else "yellow" if percent >= low else "red"


def badge(s, label, thresholds):
    return {"schemaVersion": 1, "label": label, "message": f"{s.percent}%",
            "color": colour(s.percent, thresholds)}


def summary(s, label):
    lines = [f"### {label.capitalize()}: {s.percent}%", "",
             f"{s.detected} of {s.total} mutants detected.", ""]
    if len(s.packages) > 1:
        lines += ["| Package | Detected | Score |", "|---|---:|---:|"]
        for name, (detected, total) in sorted(s.packages.items()):
            lines.append(f"| `{name}` | {detected}/{total} | {round(100 * detected / total)}% |")
        lines.append("")
    return "\n".join(lines)


def badge_url(server, repository, branch, path):
    raw = f"https://raw.githubusercontent.com/{repository}/{branch}/{path}" if server == "https://github.com" \
        else f"{server}/{repository}/raw/{branch}/{path}"  # GitHub Enterprise Server
    return "https://img.shields.io/endpoint?url=" + urllib.parse.quote(raw, safe="")


def git(*args, cwd, check=True):
    return subprocess.run(["git", *args], cwd=cwd, check=check, text=True, capture_output=True)


def publish(remote, branch, files, message, attempts=3):
    """Writes files ({path in branch: source path, or None for a directory to remove}) onto branch as
    its only commit, keeping whatever else the branch holds; retries if another run pushed meanwhile."""
    for attempt in range(attempts):
        with tempfile.TemporaryDirectory() as work:
            git("init", "-q", cwd=work)
            fetched = git("fetch", "-q", "--depth=1", remote, branch, cwd=work, check=False).returncode == 0
            lease = ""
            if fetched:
                git("checkout", "-q", "FETCH_HEAD", cwd=work)
                lease = git("rev-parse", "FETCH_HEAD", cwd=work).stdout.strip()
            git("checkout", "-q", "--orphan", "pitest-badge-publish", cwd=work)
            for target, source in files.items():
                dest = Path(work, target)
                if dest.is_dir():
                    shutil.rmtree(dest)
                dest.parent.mkdir(parents=True, exist_ok=True)
                if Path(source).is_dir():
                    shutil.copytree(source, dest)
                else:
                    shutil.copyfile(source, dest)
            git("add", "-A", cwd=work)
            git("-c", f"user.name={BOT[0]}", "-c", f"user.email={BOT[1]}",
                "commit", "-q", "--allow-empty", "-m", message, cwd=work)
            push = git("push", "-q", f"--force-with-lease={branch}:{lease}", remote,
                       f"HEAD:refs/heads/{branch}", cwd=work, check=False)
            if push.returncode == 0:
                return
            error = push.stderr.strip()
        print(f"::warning::Push to {branch} failed (attempt {attempt + 1}): {error}")
    raise SystemExit(f"::error::Couldn't push to {branch}. The job needs `permissions: contents: write`.")


def thresholds_input(text):
    low, high = (int(v) for v in text.replace(" ", "").split(","))
    if not 0 <= low <= high <= 100:
        raise ValueError
    return low, high


def report_dirs(reports):
    """The HTML report folders next to each mutations.xml that has one."""
    return [r.parent for r in reports if (r.parent / "index.html").exists()]


def main(env=os.environ):
    def get(name, default=""):
        return env.get(f"INPUT_{name.upper().replace('-', '_')}", default).strip()

    try:
        thresholds = thresholds_input(get("thresholds", "60,80"))
    except ValueError:
        raise SystemExit("::error::thresholds must be two percentages, low then high, e.g. 60,80")

    reports = find_reports(get("reports").split())
    if not reports:
        raise SystemExit("::error::No mutations.xml found. Run Pitest with the XML output format "
                         "(Gradle: outputFormats = listOf(\"XML\", \"HTML\"); Maven: <outputFormats>XML,HTML</outputFormats>), "
                         "or point `reports` at it.")
    s = score(reports)
    label = get("label", "mutation coverage")
    badge_path = get("badge-file", "pitest.json")
    badge_branch = get("badge-branch", "badges")

    out = Path(get("output-dir", "pitest-badge"))
    out.mkdir(parents=True, exist_ok=True)
    (out / "pitest.json").write_text(json.dumps(badge(s, label, thresholds)) + "\n")
    print(f"{label}: {s.percent}% ({s.detected}/{s.total}) from {', '.join(map(str, reports))}")

    server = env.get("GITHUB_SERVER_URL", "https://github.com")
    repository = env.get("GITHUB_REPOSITORY", "")
    url = badge_url(server, repository, badge_branch, badge_path)
    outputs = {"score": s.percent, "detected": s.detected, "total": s.total,
               "color": colour(s.percent, thresholds), "badge-file": out / "pitest.json", "badge-url": url}
    if "GITHUB_OUTPUT" in env:
        with open(env["GITHUB_OUTPUT"], "a") as f:
            f.writelines(f"{k}={v}\n" for k, v in outputs.items())
    if "GITHUB_STEP_SUMMARY" in env:
        with open(env["GITHUB_STEP_SUMMARY"], "a") as f:
            f.write(summary(s, label) + "\n")

    if get("publish", "false").lower() != "true":
        print("Not publishing: by default only a push to the default branch does (set `publish` to override).")
        return
    remote = env.get("PITEST_BADGE_REMOTE") or \
        f"{server.replace('://', '://x-access-token:' + get('token') + '@')}/{repository}.git"
    message = f"{label}: {s.percent}% ({env.get('GITHUB_SHA', '')[:7] or 'local'})"
    if badge_branch:
        publish(remote, badge_branch, {badge_path: out / "pitest.json"}, message)
        print(f"Badge: {url}")

    if get("report", "false").lower() == "true":
        dirs = report_dirs(reports)
        if not dirs:
            print("::warning::No HTML report next to mutations.xml; add HTML to Pitest's output formats.")
            return
        pages_path = get("pages-path", "pitest").strip("/")
        files = {badge_path: out / "pitest.json"}
        if len(dirs) == 1:
            files[pages_path] = dirs[0]
        else:
            # one folder per module, named after its path
            for d in dirs:
                name = str(d.relative_to(Path.cwd()) if d.is_absolute() else d).replace(os.sep, "-")
                files[f"{pages_path}/{name}"] = d
        publish(remote, get("pages-branch", "gh-pages"), files, message)


if __name__ == "__main__":
    sys.exit(main())
