"""Versioned policy prompts and bounded structured-output contract validation."""
import json
from pathlib import Path
from .model_client import ModelProtocolError

VERSIONS = ('baseline', 'instruction-focused', 'uncertainty-aware', 'policy-workflow', 'structured')


def load_prompt(version, baseline_text, root):
    if version not in VERSIONS:
        raise ValueError('Unknown prompt version: ' + str(version))
    # Keep the historical baseline byte-identical, including for older callers.
    if version == 'baseline':
        return baseline_text
    return (Path(root) / 'prompts/phase-3' / (version + '.txt')).read_text(encoding='utf-8')


def response_schema(policy_ids):
    return {'type': 'object', 'additionalProperties': False, 'properties': {
        'answer': {'type': 'string', 'minLength': 1},
        'response_type': {'type': 'string', 'enum': ['answer', 'clarify', 'refuse', 'unknown']},
        'policy_references': {'type': 'array', 'items': {'type': 'string', 'enum': sorted(policy_ids)}}},
        'required': ['answer', 'response_type', 'policy_references']}


def parse_structured(content, policy_ids):
    try:
        result = json.loads(content)
    except (json.JSONDecodeError, TypeError) as exc:
        raise ModelProtocolError('The structured model answer is not valid JSON.') from exc
    if not isinstance(result, dict) or set(result) != {'answer', 'response_type', 'policy_references'}:
        raise ModelProtocolError('Structured answer fields do not match the required schema.')
    if not isinstance(result['answer'], str) or not result['answer'].strip() or len(result['answer']) > 8000:
        raise ModelProtocolError('Structured answer must contain nonempty bounded employee-facing text.')
    if not isinstance(result['response_type'], str) or result['response_type'] not in {'answer', 'clarify', 'refuse', 'unknown'}:
        raise ModelProtocolError('Structured response_type is invalid.')
    refs = result['policy_references']
    if not isinstance(refs, list) or any(not isinstance(p, str) or p not in policy_ids for p in refs) or len(set(refs)) != len(refs):
        raise ModelProtocolError('Structured answer contains invalid or duplicate policy identifiers.')
    return result
