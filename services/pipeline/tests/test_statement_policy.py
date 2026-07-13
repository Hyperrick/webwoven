from __future__ import annotations

from webwoven_pipeline.statement_policy import eligible_statements


def test_policy_uses_preferred_rank_and_rejects_ended_facts() -> None:
    statements = [
        _statement("normal-current", "normal"),
        _statement("normal-ended", "normal", ended=True),
        _statement("preferred-current", "preferred"),
        _statement("preferred-ended", "preferred", ended=True),
        _statement("deprecated", "deprecated"),
    ]

    eligible = eligible_statements(statements)

    assert [item["id"] for item in eligible] == ["preferred-current"]


def test_policy_keeps_all_current_normal_statements_without_preferred_rank() -> None:
    statements = [_statement("one", "normal"), _statement("two", "normal")]

    eligible = eligible_statements(statements)

    assert [item["id"] for item in eligible] == ["one", "two"]


def _statement(statement_id: str, rank: str, *, ended: bool = False) -> dict:
    qualifiers = {"P582": [{"snaktype": "value"}]} if ended else {}
    return {"id": statement_id, "rank": rank, "qualifiers": qualifiers}
