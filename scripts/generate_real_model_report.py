#!/usr/bin/env python3
"""Generate reports and unannotated Label Studio tasks for an actual model run."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.real_model_report import generate_real_reports
from scripts.generate_report import generate_reports
from src.assistant import ROOT

if __name__ == '__main__':
    try:
        summary = generate_real_reports(ROOT)
        generate_reports(ROOT)
        print(json.dumps(summary, indent=2))
    except (ValueError, OSError) as exc:
        print(f'Real report generation failed: {exc}', file=sys.stderr); sys.exit(1)
