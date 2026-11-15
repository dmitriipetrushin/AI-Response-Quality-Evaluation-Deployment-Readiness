#!/usr/bin/env python3
"""Verify required artifacts, task bindings, documentation metrics, and report freshness."""
import argparse
import csv
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote
from urllib.parse import urlsplit
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

if __package__:
    from .validate_dataset import ROOT, CLASSIFICATIONS, DatasetValidationError, load_dataset
    from .generate_report import INPUTS, calculate_metrics, markdown_report, html_dashboard
    from .generate_label_studio import build_tasks
else:
    from validate_dataset import ROOT, CLASSIFICATIONS, DatasetValidationError, load_dataset
    from generate_report import INPUTS, calculate_metrics, markdown_report, html_dashboard
    from generate_label_studio import build_tasks

REQUIRED = [
    'README.md', 'LICENSE', '.gitignore', 'THIRD_PARTY_NOTICES.md',
    *INPUTS, 'scripts/validate_dataset.py', 'scripts/generate_report.py',
    'scripts/generate_label_studio.py', 'scripts/verify_project.py', 'tests/test_evaluation.py',
    'label-studio/labeling-config.xml', 'label-studio/import-tasks.json', 'label-studio/setup-guide.md',
    'quality-assurance/evaluation-rubric.md', 'quality-assurance/test-plan.md',
    'project-management/project-charter.md', 'project-management/project-roadmap.md',
    'project-management/product-backlog.csv', 'project-management/risk-register.csv',
    'project-management/stakeholder-plan.md', 'project-management/budget-estimate.md',
    'project-management/executive-status-report.md', 'project-management/lessons-learned.md',
    'reports/quality-report.md', 'reports/dashboard.html', 'reports/metrics.json',
    'reports/completion-report.md', 'portfolio/case-study.md',
    'portfolio/executive-summary.md', 'portfolio/resume-description.md',
]
PRESENTATIONS = ['README.md', 'portfolio/case-study.md', 'portfolio/executive-summary.md',
                 'project-management/executive-status-report.md']


class OfflineHTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.remote = []
        self.details = 0
        self.lang = None
        self.has_viewport = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'html':
            self.lang = attrs.get('lang')
        if tag == 'meta' and attrs.get('name') == 'viewport':
            self.has_viewport = True
        if tag == 'details':
            self.details += 1
        for field in ['src', 'href']:
            value = attrs.get(field, '')
            if value.startswith(('http:', 'https:', '//')):
                if not (tag == 'a' and field == 'href' and urlsplit(value).hostname in {'127.0.0.1', 'localhost', '::1'}):
                    self.remote.append(value)


def verify_project(root=ROOT):
    root = Path(root).resolve()
    for name in REQUIRED:
        path = root / name
        if not path.is_file() or not path.stat().st_size:
            raise DatasetValidationError(f'Missing or empty artifact: {name}')
    dataset = load_dataset(root)
    policies = (root / 'data/company-policies.md').read_text(encoding='utf-8')
    word_count = len(policies.split())
    if not 1500 <= word_count <= 2500:
        raise DatasetValidationError(f'Policy word count outside 1500–2500: {word_count}')
    tasks = json.loads((root / 'label-studio/import-tasks.json').read_text(encoding='utf-8'))
    if tasks != build_tasks(dataset):
        raise DatasetValidationError('Label Studio tasks differ from current authoritative inputs')
    xml = ET.parse(root / 'label-studio/labeling-config.xml').getroot()
    names = [node.attrib['name'] for node in xml.iter() if 'name' in node.attrib]
    if len(names) != len(set(names)):
        raise DatasetValidationError('Duplicate annotation tag names')
    texts = {node.attrib['name']: node for node in xml.iter('Text')}
    for control in [*xml.iter('Choices'), *xml.iter('TextArea')]:
        if control.attrib.get('toName') not in texts:
            raise DatasetValidationError('Annotation control does not bind to a Text object')
        if control.attrib.get('required') != 'true':
            raise DatasetValidationError('Annotation controls must require a response')
    choices = {node.attrib['name']: node for node in xml.iter('Choices')}
    for key, expected in [('classification', set(CLASSIFICATIONS)), ('critical_failure', {'Yes', 'No'})]:
        if {child.attrib['value'] for child in choices[key]} != expected:
            raise DatasetValidationError(f'Invalid {key} annotation choices')
        if choices[key].attrib.get('choice') not in {'single', 'single-radio'}:
            raise DatasetValidationError('Primary and critical annotation choices must be exclusive')
    for text in texts.values():
        value = text.attrib.get('value', '')
        if not value.startswith('$') or any(value[1:] not in t['data'] for t in tasks):
            raise DatasetValidationError('Missing Label Studio task binding')
    metrics = calculate_metrics(dataset)
    metrics['input_sha256'] = {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in INPUTS}
    if json.loads((root / 'reports/metrics.json').read_text()) != metrics:
        raise DatasetValidationError('Metrics JSON is stale')
    if (root / 'reports/quality-report.md').read_text(encoding='utf-8') != markdown_report(dataset, metrics):
        raise DatasetValidationError('Markdown report is stale')
    dashboard = (root / 'reports/dashboard.html').read_text(encoding='utf-8')
    from scripts.real_model_report import real_summary
    phase3_path = root / 'reports/phase-3-metrics.json'
    phase3_summary = json.loads(phase3_path.read_text()) if phase3_path.exists() else None
    if dashboard != html_dashboard(dataset, metrics, real_summary(root), phase3_summary):
        raise DatasetValidationError('HTML report is stale')
    parser = OfflineHTML()
    parser.feed(dashboard)
    if parser.remote or parser.details != 30 or parser.lang != 'en' or not parser.has_viewport:
        raise DatasetValidationError('HTML must be offline, accessible by language, responsive, and include 30 cases')
    for filename in PRESENTATIONS:
        text = (root / filename).read_text(encoding='utf-8')
        for token in [f"{metrics['correct_rate']:.1f}%", f"{metrics['unsupported_rate']:.1f}%",
                      f"{metrics['coverage']:.1f}%", f"{metrics['counts']['Correct']}/{metrics['total']}",
                      f"{metrics['counts']['Unsupported']}/{metrics['total']}"]:
            if token not in text:
                raise DatasetValidationError(f'{filename}: missing or stale metric {token}')
        if 'synthetic' not in text.lower() or 'simulated' not in text.lower():
            raise DatasetValidationError(f'{filename}: missing provenance disclosure')
        if metrics['decision'].startswith('NO-GO') and 'NO-GO' not in text:
            raise DatasetValidationError(f'{filename}: missing no-go recommendation')
    for filename, minimum in [('project-management/product-backlog.csv', 15), ('project-management/risk-register.csv', 10)]:
        with (root / filename).open(newline='', encoding='utf-8') as stream:
            rows = list(csv.DictReader(stream))
        if len(rows) < minimum or any(not v for row in rows for v in row.values()):
            raise DatasetValidationError(f'{filename}: incomplete records')
    # Repository Markdown links only; web links are references and need no network to verify.
    for path in root.rglob('*.md'):
        if any(part.startswith('.') for part in path.relative_to(root).parts):
            continue
        text = path.read_text(encoding='utf-8')
        for link in re.findall(r'\[[^\]]+\]\(([^)]+)\)', text):
            if ':' in link or link.startswith('#'):
                continue
            target = unquote(link.split('#', 1)[0])
            if target and not (path.parent / target).exists():
                raise DatasetValidationError(f'{path.relative_to(root)}: broken link {link}')
    return {'required_artifacts': len(REQUIRED), 'policy_words': word_count,
            'label_studio_tasks': len(tasks), 'reports_fresh': True,
            'presentation_metrics_consistent': True, 'local_markdown_links_valid': True}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        print(json.dumps(verify_project(args.root), indent=2))
    except (OSError, ValueError, KeyError, ET.ParseError) as exc:
        print(f'Project verification failed: {exc}', file=sys.stderr)
        sys.exit(1)
