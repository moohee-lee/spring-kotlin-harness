#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from initializr_common import CHECKLIST, InitializrError, parse_checklist, write_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Initializr dependency 체크박스 선택값을 파싱합니다.")
    parser.add_argument("--checklist", type=Path, default=Path(CHECKLIST))
    parser.add_argument("--selection-json", type=Path)
    parser.add_argument("--format", choices=["json", "csv"], default="json")
    args = parser.parse_args()

    selection = parse_checklist(args.checklist)
    if args.selection_json:
        write_json(args.selection_json, selection)
        print(f"Wrote {args.selection_json}")
    elif args.format == "csv":
        print(",".join(selection["dependencies"]))
    else:
        import json

        print(json.dumps(selection, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except InitializrError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
