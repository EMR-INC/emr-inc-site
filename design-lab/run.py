#!/usr/bin/env python3
"""Run every study. `python3 run.py` from design-lab/, or name one: `python3 run.py palette`."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STUDIES = ["palette", "forms", "layout", "collage"]

def main():
    want = sys.argv[1:] or STUDIES
    bad = [w for w in want if w not in STUDIES]
    if bad:
        sys.exit(f"no such study: {', '.join(bad)}. have: {', '.join(STUDIES)}")
    for name in want:
        r = subprocess.run([sys.executable, str(ROOT / "studies" / f"{name}.py")])
        if r.returncode:
            sys.exit(f"\n  {name} failed")
    print(f"\n  sheets in {ROOT / 'studies' / 'out'}")

if __name__ == "__main__":
    main()
