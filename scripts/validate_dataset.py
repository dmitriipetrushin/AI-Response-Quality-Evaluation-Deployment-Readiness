#!/usr/bin/env python3
"""Validate the synthetic baseline and normalize CSV booleans without dependencies."""
import argparse
import csv
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATEGORY_COUNTS = {'factual': 10, 'multi_step': 5, 'ambiguous': 5,
                   'out_of_scope': 5, 'sensitive': 5}
CLASSIFICATIONS = ('Correct', 'Partially correct', 'Incorrect', 'Unsupported')
CASE_FIELDS = {'test_id', 'category', 'employee_question', 'policy_references',
               'policy_context', 'reference_answer', 'expected_behavior',
               'risk_level', 'acceptance_criteria'}
RESPONSE_FIELDS = {'test_id', 'response_source', 'candidate_response'}
EVALUATION_FIELDS = {'test_id', 'category', 'response_source', 'classification',
                     'critical_failure', 'policy_references',
                     'evaluation_rationale', 'evaluation_method'}


class DatasetValidationError(ValueError):
    """Input cannot be safely evaluated or reported."""


@dataclass
class Dataset:
    cases: list
    responses: list
    evaluations: list


def validate_records(cases, responses, evaluations, policies):
    """Validate relational integrity and baseline provenance; return normalized copies.

    This checks structure and traceability, not whether a response is semantically
    correct. Those decisions are the explicitly authored simulated reviews.
    """
    errors = []
    record_groups = [(cases, CASE_FIELDS, 'case'),
                     (responses, RESPONSE_FIELDS, 'response'),
                     (evaluations, EVALUATION_FIELDS, 'evaluation')]
    for records, fields, kind in record_groups:
        if not isinstance(records, list) or any(not isinstance(r, dict) for r in records):
            raise DatasetValidationError(f'{kind} records must be a list of objects')
        for index, row in enumerate(records, 1):
            missing = fields - row.keys()
            if missing:
                errors.append(f'{kind} {index}: missing fields {sorted(missing)}')
            for field in fields - {'critical_failure', 'policy_references'}:
                if not isinstance(row.get(field), str) or not row.get(field, '').strip():
                    errors.append(f'{kind} {index}: {field} must be nonempty text')
        ids = [r.get('test_id') for r in records]
        if any(not isinstance(i, str) for i in ids):
            errors.append(f'{kind}: test IDs must be strings')
        elif len(ids) != len(set(ids)):
            errors.append(f'{kind}: duplicate test IDs')
    if errors:
        raise DatasetValidationError('\n'.join(errors))
    if len(cases) != 30:
        errors.append(f'Expected exactly 30 cases; found {len(cases)}')
    if Counter(c['category'] for c in cases) != Counter(CATEGORY_COUNTS):
        errors.append('Incorrect category counts')
    case_map = {r['test_id']: r for r in cases}
    response_map = {r['test_id']: r for r in responses}
    evaluation_map = {r['test_id']: r for r in evaluations}
    for kind, mapping in [('responses', response_map), ('evaluations', evaluation_map)]:
        if set(mapping) != set(case_map):
            errors.append(f'{kind}: missing {sorted(set(case_map)-set(mapping))}; '
                          f'orphaned {sorted(set(mapping)-set(case_map))}')
    policy_ids = set(re.findall(r'^## (POL-\d{3})\b', policies, flags=re.M))
    if not policy_ids:
        errors.append('No policy identifiers found')
    behaviors = {'answer', 'answer_with_limits', 'safe_refusal', 'clarify', 'acknowledge_unknown'}
    for case in cases:
        tid = case['test_id']
        if not re.fullmatch(r'TC-\d{3}', tid):
            errors.append(f'{tid}: invalid ID format')
        if case['risk_level'] not in {'low', 'medium', 'high'}:
            errors.append(f'{tid}: invalid risk level')
        if case['expected_behavior'] not in behaviors:
            errors.append(f'{tid}: invalid expected behavior')
        refs = case.get('policy_references')
        if not isinstance(refs, list) or any(not isinstance(p, str) for p in refs):
            errors.append(f'{tid}: policy_references must be a list of policy IDs')
        else:
            if len(refs) != len(set(refs)) or set(refs) - policy_ids:
                errors.append(f'{tid}: duplicate or unknown referenced policies')
            if not refs and case['category'] != 'out_of_scope':
                errors.append(f'{tid}: in-scope case must reference a policy')
        if any(excerpt not in policies for excerpt in case['policy_context'].split('\n\n')):
            errors.append(f'{tid}: context must contain verbatim policy excerpts')
    for row in responses:
        if row['response_source'] != 'synthetic_fixture':
            errors.append(f"{row['test_id']}: baseline response source must be synthetic_fixture")
    normalized = []
    for row in evaluations:
        tid = row['test_id']
        if row['classification'] not in CLASSIFICATIONS:
            errors.append(f'{tid}: invalid classification')
        critical = row['critical_failure']
        if type(critical) is bool:
            pass
        elif isinstance(critical, str) and critical in {'true', 'false'}:
            critical = critical == 'true'
        else:
            errors.append(f'{tid}: critical_failure must be true or false')
        if row['classification'] == 'Correct' and critical is True:
            errors.append(f'{tid}: a Correct response cannot be a critical failure')
        if row['evaluation_method'] != 'simulated_review':
            errors.append(f'{tid}: baseline evaluation_method must be simulated_review')
        if row['response_source'] != 'synthetic_fixture':
            errors.append(f'{tid}: baseline evaluation source must be synthetic_fixture')
        refs = row['policy_references']
        if not isinstance(refs, str):
            errors.append(f'{tid}: CSV policy_references must be semicolon-separated text')
        else:
            actual_refs = refs.split(';') if refs else []
            case = case_map.get(tid)
            if set(actual_refs) - policy_ids:
                errors.append(f'{tid}: unknown referenced policies in evaluation')
            if case and actual_refs != case.get('policy_references'):
                errors.append(f'{tid}: evaluation policy references disagree with case')
        case = case_map.get(tid)
        if case and row['category'] != case['category']:
            errors.append(f'{tid}: evaluation category disagrees with case')
        normalized.append({**row, 'critical_failure': critical})
    if errors:
        raise DatasetValidationError('\n'.join(errors))
    return Dataset(cases, responses, normalized)


def load_dataset(root=ROOT):
    root = Path(root)
    try:
        cases = json.loads((root / 'data/test-cases.json').read_text(encoding='utf-8'))
        responses = json.loads((root / 'data/candidate-responses.json').read_text(encoding='utf-8'))
        with (root / 'data/evaluation-results.csv').open(encoding='utf-8', newline='') as stream:
            reader = csv.DictReader(stream)
            if not EVALUATION_FIELDS.issubset(reader.fieldnames or []):
                raise DatasetValidationError('Evaluation CSV is missing required columns')
            if len(reader.fieldnames) != len(set(reader.fieldnames)):
                raise DatasetValidationError('Evaluation CSV has duplicate columns')
            evaluations = list(reader)
            if any(None in row or any(value is None for value in row.values()) for row in evaluations):
                raise DatasetValidationError('Evaluation CSV contains malformed rows')
        policies = (root / 'data/company-policies.md').read_text(encoding='utf-8')
    except (OSError, UnicodeError, json.JSONDecodeError, csv.Error) as exc:
        raise DatasetValidationError(f'Cannot load dataset: {exc}') from exc
    return validate_records(cases, responses, evaluations, policies)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        dataset = load_dataset(args.root)
    except DatasetValidationError as exc:
        print(f'INVALID: {exc}', file=sys.stderr)
        return 1
    print(f'VALID: {len(dataset.cases)} cases, {len(dataset.responses)} synthetic responses, '
          f'{len(dataset.evaluations)} simulated reviews; categories and policy references verified.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
