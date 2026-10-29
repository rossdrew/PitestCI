import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import badge  # noqa: E402


def report(path, *mutations):
    """Writes a mutations.xml of (class, detected, status) triples."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = "".join(
        f"<mutation detected='{str(d).lower()}' status='{s}'><mutatedClass>{c}</mutatedClass></mutation>"
        for c, d, s in mutations)
    path.write_text(f"<?xml version='1.0'?><mutations>{rows}</mutations>")
    return path


def git(*args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, check=True, text=True, capture_output=True).stdout.strip()


class ScoreTest(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())

    def test_counts_mutants_marked_detected(self):
        r = report(self.dir / "mutations.xml",
                   ("a.B", True, "KILLED"), ("a.B", True, "TIMED_OUT"), ("a.B", False, "SURVIVED"),
                   ("a.B", False, "NO_COVERAGE"))
        s = badge.score([r])
        self.assertEqual((2, 4, 50), (s.detected, s.total, s.percent))

    def test_adds_modules_together_and_groups_by_package(self):
        one = report(self.dir / "one/mutations.xml", ("x.y.A", True, "KILLED"), ("x.y.A", False, "SURVIVED"))
        two = report(self.dir / "two/mutations.xml", ("x.z.B", True, "KILLED"), ("Top", True, "KILLED"))
        s = badge.score([one, two])
        self.assertEqual((3, 4, 75), (s.detected, s.total, s.percent))
        self.assertEqual({"x.y": [1, 2], "x.z": [1, 1], "(default)": [1, 1]}, dict(s.packages))

    def test_no_mutants_scores_zero(self):
        self.assertEqual(0, badge.score([report(self.dir / "mutations.xml")]).percent)

    def test_rounds_to_the_nearest_percent(self):
        r = report(self.dir / "mutations.xml", *[("A", True, "KILLED")] * 2, ("A", False, "SURVIVED"))
        self.assertEqual(67, badge.score([r]).percent)


class BadgeTest(unittest.TestCase):
    def test_colour_changes_at_the_thresholds(self):
        self.assertEqual(["red", "yellow", "yellow", "brightgreen"],
                         [badge.colour(p, (60, 80)) for p in (59, 60, 79, 80)])

    def test_thresholds_are_two_ordered_percentages(self):
        self.assertEqual((50, 90), badge.thresholds_input(" 50, 90 "))
        for bad in ("90,50", "80", "a,b", "-1,50", "50,101"):
            with self.assertRaises(ValueError, msg=bad):
                badge.thresholds_input(bad)

    def test_badge_is_a_shields_endpoint(self):
        s = badge.Score(detected=3, total=4)
        self.assertEqual({"schemaVersion": 1, "label": "mutants", "message": "75%", "color": "yellow"},
                         badge.badge(s, "mutants", (60, 80)))

    def test_badge_url_reads_the_raw_file(self):
        self.assertEqual("https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com"
                         "%2Fo%2Fr%2Fbadges%2Fpitest.json",
                         badge.badge_url("https://github.com", "o/r", "badges", "pitest.json"))
        self.assertIn("https%3A%2F%2Fgit.example.com%2Fo%2Fr%2Fraw%2Fbadges%2Fpitest.json",
                      badge.badge_url("https://git.example.com", "o/r", "badges", "pitest.json"))

    def test_summary_tables_packages_only_when_there_are_several(self):
        one = badge.Score(1, 2)
        one.packages["p"] = [1, 2]
        self.assertNotIn("| Package", badge.summary(one, "mutation coverage"))
        one.packages["q"] = [2, 2]
        text = badge.summary(one, "mutation coverage")
        self.assertIn("### Mutation coverage: 50%", text)
        self.assertIn("| `q` | 2/2 | 100% |", text)


class FindReportsTest(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        report(self.dir / "a/build/reports/pitest/mutations.xml")
        report(self.dir / "b/target/pit-reports/mutations.xml")
        report(self.dir / ".git/mutations.xml")
        report(self.dir / "node_modules/x/mutations.xml")

    def test_finds_every_report_outside_vcs_and_dependencies(self):
        self.assertEqual(["a/build/reports/pitest/mutations.xml", "b/target/pit-reports/mutations.xml"],
                         [str(p.relative_to(self.dir)) for p in badge.find_reports([], self.dir)])

    def test_globs_choose_reports(self):
        found = badge.find_reports(["**/target/**/mutations.xml"], self.dir)
        self.assertEqual(["b/target/pit-reports/mutations.xml"], [str(p.relative_to(self.dir)) for p in found])


class PublishTest(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.remote = self.dir / "remote.git"
        git("init", "-q", "--bare", str(self.remote), cwd=self.dir)
        self.badge = self.dir / "pitest.json"
        self.badge.write_text("{}")

    def branch(self, name):
        clone = Path(tempfile.mkdtemp())
        git("clone", "-q", "-b", name, str(self.remote), str(clone), cwd=self.dir)
        return clone

    def test_creates_the_branch(self):
        badge.publish(str(self.remote), "badges", {"pitest.json": self.badge}, "first")
        self.assertEqual("{}", (self.branch("badges") / "pitest.json").read_text())

    def test_keeps_one_commit_and_other_files(self):
        badge.publish(str(self.remote), "badges", {"pitest.json": self.badge}, "first")
        clone = self.branch("badges")
        (clone / "other.json").write_text("mine")
        git("add", ".", cwd=clone)
        git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "other", cwd=clone)
        git("push", "-q", cwd=clone)

        self.badge.write_text('{"v": 2}')
        badge.publish(str(self.remote), "badges", {"pitest.json": self.badge}, "second")
        clone = self.branch("badges")
        self.assertEqual("1", git("rev-list", "--count", "HEAD", cwd=clone))
        self.assertEqual("mine", (clone / "other.json").read_text())
        self.assertEqual('{"v": 2}', (clone / "pitest.json").read_text())

    def test_replaces_a_folder_rather_than_merging_into_it(self):
        old, new = self.dir / "old", self.dir / "new"
        (old / "gone").mkdir(parents=True)
        (old / "gone/index.html").write_text("old")
        new.mkdir()
        (new / "index.html").write_text("new")
        badge.publish(str(self.remote), "site", {"pitest": old}, "first")
        badge.publish(str(self.remote), "site", {"pitest": new}, "second")
        clone = self.branch("site")
        self.assertEqual(["index.html"], sorted(p.name for p in (clone / "pitest").iterdir()))

    def test_gives_up_with_a_permissions_hint(self):
        with self.assertRaises(SystemExit) as e:
            badge.publish(str(self.dir / "missing.git"), "badges", {"pitest.json": self.badge}, "m", attempts=1)
        self.assertIn("contents: write", str(e.exception))


class MainTest(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.remote = self.dir / "remote.git"
        git("init", "-q", "--bare", str(self.remote), cwd=self.dir)
        self.workspace = self.dir / "ws"
        report(self.workspace / "build/reports/pitest/mutations.xml", ("p.A", True, "KILLED"), ("p.A", False, "SURVIVED"))
        (self.workspace / "build/reports/pitest/index.html").write_text("report")
        self.outputs = self.dir / "outputs"
        self.outputs.touch()

    def run_main(self, **inputs):
        env = {"GITHUB_OUTPUT": str(self.outputs), "GITHUB_REPOSITORY": "o/r", "PITEST_BADGE_REMOTE": str(self.remote),
               **{f"INPUT_{k.upper()}": v for k, v in inputs.items()}}
        cwd = Path.cwd()
        try:
            os.chdir(self.workspace)
            badge.main(env)
        finally:
            os.chdir(cwd)

    def branches(self):
        return git("branch", "--format=%(refname:short)", cwd=self.remote).split()

    def test_writes_outputs_and_badge_without_publishing_by_default(self):
        self.run_main()
        outputs = dict(line.split("=", 1) for line in self.outputs.read_text().splitlines())
        self.assertEqual(("50", "1", "2", "red"), (outputs["score"], outputs["detected"], outputs["total"], outputs["color"]))
        self.assertEqual("50%", json.loads((self.workspace / "pitest-badge/pitest.json").read_text())["message"])
        self.assertEqual([], self.branches())

    def outputs_dict(self):
        return dict(line.split("=", 1) for line in self.outputs.read_text().splitlines())

    def test_publishes_the_badge(self):
        self.run_main(publish="true", thresholds="40,90")
        self.assertEqual(["badges"], self.branches())
        self.assertEqual("false", self.outputs_dict()["pages"])

    def test_report_builds_a_pages_site_with_the_badge(self):
        self.run_main(publish="true", report="true", pages_path="mutants")
        site = self.workspace / "pitest-site"
        self.assertEqual(["mutants/index.html", "mutants/mutations.xml", "pitest.json"],
                         sorted(str(p.relative_to(site)) for p in site.rglob("*") if p.is_file()))
        self.assertEqual(("pitest-site", "true"), (self.outputs_dict()["site-dir"], self.outputs_dict()["pages"]))
        self.assertEqual(["badges"], self.branches(), "the report isn't pushed anywhere")

    def test_a_report_without_publishing_builds_the_site_but_doesnt_upload_it(self):
        self.run_main(report="true")
        self.assertTrue((self.workspace / "pitest-site/pitest/index.html").exists())
        self.assertEqual("false", self.outputs_dict()["pages"])

    def test_report_without_html_warns_and_has_no_site(self):
        (self.workspace / "build/reports/pitest/index.html").unlink()
        self.run_main(publish="true", report="true")
        self.assertEqual(("", "false"), (self.outputs_dict()["site-dir"], self.outputs_dict()["pages"]))

    def test_modules_get_a_folder_each(self):
        report(self.workspace / "other/build/reports/pitest/mutations.xml", ("q.B", True, "KILLED"))
        (self.workspace / "other/build/reports/pitest/index.html").write_text("other")
        self.run_main(report="true")
        site = self.workspace / "pitest-site/pitest"
        self.assertEqual(["build-reports-pitest", "other-build-reports-pitest"], sorted(p.name for p in site.iterdir()))

    def test_fails_clearly_without_a_report(self):
        empty = self.dir / "empty"
        empty.mkdir()
        self.workspace = empty
        with self.assertRaises(SystemExit) as e:
            self.run_main()
        self.assertIn("No mutations.xml found", str(e.exception))


if __name__ == "__main__":
    unittest.main()
