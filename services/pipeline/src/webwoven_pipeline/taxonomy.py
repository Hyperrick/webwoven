from __future__ import annotations

CATEGORIES = (
    "people",
    "history_society",
    "science_technology",
    "nature_life",
    "places_architecture",
    "art_design",
    "literature_language",
    "music_performance",
    "film_media",
    "sports_games",
)

CATEGORY_LABELS = {
    "people": "People",
    "history_society": "History & Society",
    "science_technology": "Science & Technology",
    "nature_life": "Nature & Life",
    "places_architecture": "Places & Architecture",
    "art_design": "Art & Design",
    "literature_language": "Literature & Language",
    "music_performance": "Music & Performance",
    "film_media": "Film & Media",
    "sports_games": "Sports & Games",
}


def category_sort_key(category: str) -> int:
    try:
        return CATEGORIES.index(category)
    except ValueError as exc:
        raise ValueError(f"unknown category: {category}") from exc
