"""Small, completely local English spelling corrector for task text.

Uses pyspellchecker's bundled frequency dictionary. There is no network call and
no cloud service. It intentionally only auto-corrects high-confidence words:
short words, all-caps acronyms, mixed-case names and title-case proper nouns in
the middle of a sentence are left alone.
"""

from __future__ import annotations

import re
from typing import List, Tuple

from spellchecker import SpellChecker

_WORD = re.compile(r"[A-Za-z][A-Za-z'’]*")
_KEEP = {
    "yonjiz",
    "hussein",
    "hussien",
    "nael",
    "alomar",
    "jordan",
    "amman",
    "app",
    "apps",
    "todo",
    "todos",
    "email",
    "login",
    "admin",
    "deadline",
    "calendar",
    "password",
    "username",
}
# High-frequency typos that are safe to fix even at the start of a title.
_COMMON = {
    "teh": "the",
    "adn": "and",
    "recieve": "receive",
    "breif": "brief",
    "studdy": "study",
    "lieks": "likes",
    "woudl": "would",
    "jsut": "just",
    "tommorow": "tomorrow",
    "definately": "definitely",
    "seperate": "separate",
    "occured": "occurred",
    "wich": "which",
    "becuase": "because",
    "beacuse": "because",
    "thier": "their",
    "wierd": "weird",
    "accomodate": "accommodate",
}
_SPELL = SpellChecker(language="en")


def _distance(left: str, right: str) -> int:
    """Levenshtein distance, small strings only."""
    if left == right:
        return 0
    if len(left) < len(right):
        left, right = right, left
    previous = list(range(len(right) + 1))
    for i, ch_left in enumerate(left, 1):
        current = [i]
        for j, ch_right in enumerate(right, 1):
            current.append(
                min(
                    current[-1] + 1,
                    previous[j] + 1,
                    previous[j - 1] + (ch_left != ch_right),
                )
            )
        previous = current
    return previous[-1]


def _case_like(original: str, suggestion: str) -> str:
    if original.isupper():
        return suggestion.upper()
    if original[:1].isupper():
        return suggestion[:1].upper() + suggestion[1:]
    return suggestion


def _protected(word: str, text: str, start: int) -> bool:
    lower = word.lower()
    if lower in _KEEP:
        return True
    if len(lower) < 3 or word.isupper() or any(ch.isupper() for ch in word[1:]):
        return True
    # Proper nouns in the middle of a sentence are probably names/places.
    sentence_start = start == 0 or text[start - 1] in ".?!\n"
    if word[:1].isupper() and start > 0 and not sentence_start:
        return True
    return False


def correct_text(text: str) -> Tuple[str, List[Tuple[str, str]]]:
    """Return corrected text plus (original, replacement) pairs."""
    if not text or not text.strip():
        return text, []

    replacements: List[Tuple[int, int, str, str, str]] = []
    for match in _WORD.finditer(text):
        original = match.group(0)
        if _protected(original, text, match.start()):
            continue
        lower = original.lower()
        if lower in _COMMON:
            suggestion = _COMMON[lower]
        else:
            # Unfamiliar capitalized words are usually names or brands. Only
            # lowercase words, and the curated list above, are auto-corrected.
            if original[:1].isupper():
                continue
            if _SPELL.known([lower]):
                continue
            suggestion = _SPELL.correction(lower)
        if not suggestion or suggestion == lower:
            continue
        if lower not in _COMMON:
            distance = _distance(lower, suggestion)
            if distance > 2 or (distance == 2 and len(lower) < 6):
                continue
            try:
                if _SPELL.word_frequency[suggestion] < 10_000:
                    continue
            except KeyError:
                continue
        replacement = _case_like(original, suggestion)
        replacements.append((match.start(), match.end(), original, replacement, suggestion))

    if not replacements:
        return text, []

    corrected = text
    for start, end, _original, replacement, _suggestion in reversed(replacements):
        corrected = corrected[:start] + replacement + corrected[end:]

    changes = [(original, replacement) for _s, _e, original, replacement, _sug in replacements]
    return corrected, changes
