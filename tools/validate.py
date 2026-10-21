#!/usr/bin/env python3
"""Check one week's audit folder before it is committed.

    python3 tools/validate.py reports/2026-10-26

Prints OK, or a list of problems and exits with status 1.
Evidence written as `page:field.path` = value is checked against the raw JSON.
"""

import json
import os
import re
import sys

HEURISTICS = [
    "Visibility of system status",
    "Match between system and the real world",
    "User control and freedom",
    "Consistency and standards",
    "Error prevention",
    "Recognition rather than recall",
    "Flexibility and efficiency of use",
    "Aesthetic and minimalist design",
    "Help users recognise, diagnose and recover from errors",
    "Help and documentation",
]
SEVERITIES = {"0", "1", "2", "3", "4", "not judged"}
EVIDENCE_RE = re.compile(r"`(\w+):([\w.]+)`\s*=\s*((?:\\\||[^;|])+)")
CELL_SPLIT = re.compile(r"(?<!\\)\|")


def lookup(data, path):
    for root in (data, data.get("facts") or {}):
        node, ok = root, True
        for part in path.split("."):
            if isinstance(node, dict) and part in node:
                node = node[part]
            elif isinstance(node, list) and part.isdigit() and int(part) < len(node):
                node = node[int(part)]
            else:
                ok = False
                break
        if ok:
            return True, node
    return False, None


def check_evidence(cell, raw, where, problems):
    for page, path, value in EVIDENCE_RE.findall(cell):
        if page not in raw:
            problems.append(f"{where}: evidence names page '{page}', which has no raw file")
            continue
        found, actual = lookup(raw[page], path)
        if not found:
            problems.append(f"{where}: `{page}:{path}` is not in raw/{raw[page]['_file']}")
            continue
        text = value.strip().replace("\\|", "|")
        try:
            claimed, end = json.JSONDecoder().raw_decode(text)
            text = text[:end]
        except ValueError:
            continue
        if isinstance(claimed, (bool, int, float)) or claimed is None:
            if claimed != actual:
                problems.append(f"{where}: `{page}:{path}` is {json.dumps(actual)} in the raw file, not {text}")
        elif isinstance(claimed, str) and claimed not in json.dumps(actual, ensure_ascii=False):
            problems.append(f"{where}: \"{claimed}\" is not in `{page}:{path}`")


def main(folder):
    problems = []
    base = os.path.abspath(os.path.join(folder, "..", ".."))
    with open(os.path.join(base, "config.json"), encoding="utf-8") as fh:
        config = json.load(fh)

    for site in config["sites"]:
        raw = {}
        for page in site["pages"]:
            name = f"{site['key']}-{page['key']}.json"
            path = os.path.join(folder, "raw", name)
            try:
                with open(path, encoding="utf-8") as fh:
                    raw[page["key"]] = json.load(fh)
                    raw[page["key"]]["_file"] = name
            except FileNotFoundError:
                problems.append(f"missing raw/{name}")
            except ValueError as exc:
                problems.append(f"raw/{name} is not valid JSON: {exc}")

        report = os.path.join(folder, f"{site['key']}.md")
        if not os.path.exists(report):
            problems.append(f"missing {site['key']}.md")
            continue
        with open(report, encoding="utf-8") as fh:
            text = fh.read()
        rows = {}
        for line in text.splitlines():
            cells = [c.strip() for c in CELL_SPLIT.split(line.strip().strip("|"))]
            if len(cells) >= 4 and cells[0].isdigit():
                rows[cells[1]] = cells
        for number, name in enumerate(HEURISTICS, 1):
            where = f"{site['key']}.md, heuristic {number}"
            cells = rows.get(name)
            if not cells:
                problems.append(f"{where}: no table row named '{name}'")
                continue
            if cells[2] not in SEVERITIES:
                problems.append(f"{where}: severity '{cells[2]}' is not 0-4 or 'not judged'")
            evidence = " | ".join(cells[3:])
            if cells[2] == "not judged" and "not judged from HTML" not in evidence:
                problems.append(f"{where}: 'not judged' rows must say 'not judged from HTML'")
            if cells[2] in SEVERITIES - {"not judged"} and not EVIDENCE_RE.search(evidence):
                problems.append(f"{where}: a severity needs evidence written as `page:field.path` = value")
            check_evidence(evidence, raw, where, problems)
        for heading in ("## Three suggestions for the web team", "## Since last week"):
            if heading not in text:
                problems.append(f"{site['key']}.md: missing the heading '{heading}'")

    comparison = os.path.join(folder, "comparison.md")
    if not os.path.exists(comparison):
        problems.append("missing comparison.md")
    else:
        with open(comparison, encoding="utf-8") as fh:
            text = fh.read()
        for name in HEURISTICS:
            if name not in text:
                problems.append(f"comparison.md: '{name}' is missing")

    readme = os.path.join(base, "README.md")
    with open(readme, encoding="utf-8") as fh:
        text = fh.read()
    if "<!-- scoreboard:start -->" not in text or "<!-- scoreboard:end -->" not in text:
        problems.append("README.md: the scoreboard markers are missing")

    if problems:
        print("Problems found:")
        for p in problems:
            print(" - " + p)
        sys.exit(1)
    print("OK")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python3 tools/validate.py reports/<YYYY-MM-DD>")
    main(sys.argv[1].rstrip("/"))
