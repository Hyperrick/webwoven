from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import replace
from urllib.parse import quote, urlparse

from .media_discovery_hints import WIKIPEDIA_SITE_PRIORITY
from .models import Entity


def attach_wikipedia_articles(
    entities: Iterable[Entity],
    sitelinks_by_qid: Mapping[str, Mapping[str, str]],
) -> tuple[Entity, ...]:
    """Attach one deterministic preferred Wikipedia article URL per entity."""
    return tuple(
        replace(entity, wikipedia_url=preferred_wikipedia_url(sitelinks_by_qid.get(entity.id, {})))
        for entity in entities
    )


def preferred_wikipedia_url(sitelinks: Mapping[str, str]) -> str | None:
    for site in WIKIPEDIA_SITE_PRIORITY:
        title = sitelinks.get(site, "").strip()
        if not title:
            continue
        language = site.removesuffix("wiki")
        article = quote(title.replace(" ", "_"), safe="()/:,-._~")
        return f"https://{language}.wikipedia.org/wiki/{article}"
    return None


def is_wikipedia_article_url(value: str) -> bool:
    parsed = urlparse(value)
    host = parsed.hostname or ""
    return (
        parsed.scheme == "https"
        and host.endswith(".wikipedia.org")
        and bool(host.removesuffix(".wikipedia.org"))
        and parsed.path.startswith("/wiki/")
        and len(parsed.path) > len("/wiki/")
        and not parsed.username
        and not parsed.password
        and not parsed.port
        and not parsed.query
        and not parsed.fragment
    )
