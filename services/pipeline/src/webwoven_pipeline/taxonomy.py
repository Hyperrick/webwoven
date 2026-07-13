from __future__ import annotations

CATEGORIES = (
    "history_people",
    "nature_science",
    "arts_culture",
    "places",
)

CATEGORY_LABELS = {
    "history_people": "History & People",
    "nature_science": "Nature & Science",
    "arts_culture": "Arts & Culture",
    "places": "Places",
}


def category_sort_key(category: str) -> int:
    try:
        return CATEGORIES.index(category)
    except ValueError as exc:
        raise ValueError(f"unknown category: {category}") from exc
