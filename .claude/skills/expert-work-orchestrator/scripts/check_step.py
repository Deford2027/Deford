#!/usr/bin/env python3
"""Read-only size gate. Paths must include all planned code, runtime config and tests.

This checks the supplied plan, not its completeness or semantic dependencies.
--add-functionality means new functionality will be added to every supplied path;
planned new paths may be absent. Without that flag every supplied file must exist.
"""
import argparse
import json
from pathlib import Path


def check(paths, add_functionality=False):
    paths = sorted({Path(p).resolve() for p in paths})
    issues = []
    if len(paths) > 3:
        issues.append("more_than_three_code_files")
    files = []
    for path in paths:
        if path.exists() and not path.is_file():
            raise ValueError(f"not a regular file: {path}")
        if not path.exists() and not add_functionality:
            issues.append(f"missing_final_file:{path}")
        count = len(path.read_bytes().splitlines()) if path.exists() else 0
        files.append({"path": str(path), "lines": count, "exists": path.exists()})
        if count > 800:
            issues.append(f"{'no_new_functionality' if add_functionality else 'oversize_requires_review'}:{path}")
    return {"pass": not issues, "files": files, "issues": issues,
            "scope": "supplied paths only; no semantic or completeness validation"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+")
    parser.add_argument("--add-functionality", action="store_true")
    args = parser.parse_args()
    result = check(args.paths, args.add_functionality)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
