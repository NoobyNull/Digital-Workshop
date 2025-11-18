"""Helpers for interpreting AI metadata keywords into taxonomy fields.

This module encapsulates the logic for splitting an AI-provided
``metadata_keywords`` list into a top-level category and remaining
keywords suitable for storage in ``model_metadata``.
"""

from typing import List, Optional, Tuple


# Basic set of high-level categories we currently recognize. These match
# the design examples (Animals, Vehicles, People, Nature, Abstract).
_TOP_LEVEL_CATEGORIES = {
    "animals": "Animals",
    "vehicles": "Vehicles",
    "people": "People",
    "nature": "Nature",
    "abstract": "Abstract",
}


def split_category_and_keywords(raw_keywords: List[str]) -> Tuple[Optional[str], List[str]]:
    """Split raw AI keywords into a category and remaining keywords.

    The first keyword that matches a known top-level category (case-
    insensitive) is used as the ``category``. All other non-empty
    keywords are returned in the order they appeared.

    Args:
        raw_keywords: List of keywords from the AI result.

    Returns:
        (category, keywords) where category is either a canonical
        top-level category name or None if no match is found.
    """

    if not raw_keywords:
        return None, []

    category: Optional[str] = None
    cleaned_keywords: List[str] = []

    for raw in raw_keywords:
        text = (raw or "").strip()
        if not text:
            continue

        lower = text.lower()
        if category is None and lower in _TOP_LEVEL_CATEGORIES:
            category = _TOP_LEVEL_CATEGORIES[lower]
            # Do not include the category token itself in the remaining
            # keywords list.
            continue

        cleaned_keywords.append(text)

    return category, cleaned_keywords

