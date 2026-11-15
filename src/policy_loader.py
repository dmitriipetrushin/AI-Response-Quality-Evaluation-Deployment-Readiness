"""Load the complete fictional policy corpus and its stable section identifiers."""
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PolicyDocument:
    text: str
    sha256: str
    sections: dict


def load_policies(path):
    raw = Path(path).read_bytes()
    text = raw.decode('utf-8')
    matches = list(re.finditer(r'^## (POL-\d{3}) — (.+)$', text, re.M))
    if not matches or len({m[1] for m in matches}) != len(matches):
        raise ValueError('The policy document must have unique POL-nnn section headings.')
    sections = {}
    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections[match[1]] = {'title': match[2], 'text': text[match.start():end].strip()}
    return PolicyDocument(text, hashlib.sha256(raw).hexdigest(), sections)
