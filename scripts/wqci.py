#!/usr/bin/env python3
"""wq-ci marker bodies (stdlib only).

Marker contract: first line `wq-coverage: <sha40>` or `wq-flaky: <sha40>`,
then one `path: 12-14, 20` line or test id per line; whole body <= 4000 chars.
"""
import json
import re
import sys
import xml.etree.ElementTree as ET

LIMIT = 4000
# Repo-controlled strings land in a PR comment the dispatcher parses: allow-list them.
# ASCII-only fullmatch also rules out control chars and newlines (no marker injection).
SAFE_PATH = re.compile(r"[\w./-]+", re.ASCII)
SAFE_ID = re.compile(r"[\w./:\[\]-]{1,200}", re.ASCII)


def _ranges(lines: list[int]) -> str:
    out, nums = [], sorted(set(lines))
    i = 0
    while i < len(nums):
        j = i
        while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
            j += 1
        out.append(str(nums[i]) if i == j else f"{nums[i]}-{nums[j]}")
        i = j + 1
    return ", ".join(out)


def _body(head: str, lines: list[str], limit: int) -> str | None:
    if not lines:
        return None
    body = head
    for line in lines:
        if len(body) + 1 + len(line) > limit:
            break
        body += "\n" + line
    return body if body != head else (head + "\n" + lines[0])[:limit]


def coverage_body(report: dict, sha: str, limit: int = LIMIT) -> str | None:
    stats = report.get("src_stats") or {}
    lines = [f"{p}: {_ranges(s['violation_lines'])}"
             for p, s in sorted(stats.items()) if s.get("violation_lines") and SAFE_PATH.fullmatch(p)]
    return _body(f"wq-coverage: {sha}", lines, limit)


def failed_ids(junit_xml: str) -> set[str]:
    root = ET.fromstring(junit_xml)
    return {f"{tc.get('classname')}::{tc.get('name')}" for tc in root.iter("testcase")
            if tc.find("failure") is not None or tc.find("error") is not None}


def flaky_body(first: str, last: str, sha: str, limit: int = LIMIT) -> str | None:
    flaky = sorted(i for i in failed_ids(first) - failed_ids(last) if SAFE_ID.fullmatch(i))
    return _body(f"wq-flaky: {sha}", flaky, limit)


def main(argv: list[str]) -> int:
    def read(p):
        with open(p, encoding="utf-8") as f:
            return f.read()

    match argv:
        case ["coverage-body", report, sha]:
            body = coverage_body(json.loads(read(report)), sha)
        case ["flaky-body", first, last, sha]:
            body = flaky_body(read(first), read(last), sha)
        case _:
            print("usage: wqci.py coverage-body DC_JSON SHA | flaky-body FIRST_XML LAST_XML SHA",
                  file=sys.stderr)
            return 2
    if body:
        print(body)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
