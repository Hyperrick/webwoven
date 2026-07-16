from pathlib import Path

import pytest
from webwoven_pipeline.compiler import GraphCompileError, compile_graph
from webwoven_pipeline.models import Entity
from webwoven_pipeline.wikipedia_articles import (
    attach_wikipedia_articles,
    is_wikipedia_article_url,
    preferred_wikipedia_url,
)


def test_prefers_english_and_encodes_the_article_path() -> None:
    assert (
        preferred_wikipedia_url({"dewiki": "Turing-Bombe", "enwiki": "Bombe (machine)"})
        == "https://en.wikipedia.org/wiki/Bombe_(machine)"
    )


def test_uses_the_next_supported_language_and_preserves_subpages() -> None:
    assert (
        preferred_wikipedia_url({"dewiki": "Beispiel/Technik"})
        == "https://de.wikipedia.org/wiki/Beispiel/Technik"
    )


def test_attaches_articles_without_inventing_missing_links() -> None:
    entities = (
        Entity("Q1", "One", "First", "item", "people"),
        Entity("Q2", "Two", "Second", "item", "people"),
    )

    attached = attach_wikipedia_articles(entities, {"Q1": {"enwiki": "One"}})

    assert attached[0].wikipedia_url == "https://en.wikipedia.org/wiki/One"
    assert attached[1].wikipedia_url is None


def test_rejects_non_article_and_non_wikipedia_urls() -> None:
    assert is_wikipedia_article_url("https://en.wikipedia.org/wiki/Bombe")
    assert not is_wikipedia_article_url("https://example.com/wiki/Bombe")
    assert not is_wikipedia_article_url("https://en.wikipedia.org/w/index.php?title=Bombe")


def test_compiler_rejects_an_untrusted_article_url(tmp_path: Path, registry) -> None:
    entity = Entity(
        "Q1",
        "One",
        "First",
        "item",
        "people",
        wikipedia_url="https://example.com/wiki/One",
    )

    with pytest.raises(GraphCompileError, match="invalid Wikipedia article URL"):
        compile_graph(tmp_path / "graph.sqlite3", registry, (entity,), (), ())
