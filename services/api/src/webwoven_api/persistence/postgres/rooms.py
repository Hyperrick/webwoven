"""Durable archive for completed Live Relay rooms."""

from typing import Any, cast

from sqlalchemy.dialects.postgresql import insert

from webwoven_api.persistence.postgres.database import PostgresDatabase
from webwoven_api.persistence.postgres.models import CompletedRoomRow
from webwoven_api.persistence.serialization.rooms import room_to_dict
from webwoven_api.rooms.models import Room


class PostgresCompletedRoomRepository:
    def __init__(self, database: PostgresDatabase) -> None:
        self._database = database

    async def archive(self, room: Room) -> None:
        document = cast(dict[str, Any], room_to_dict(room))
        statement = (
            insert(CompletedRoomRow)
            .values(
                code=room.code,
                graph_version=room.graph_version,
                round_id=room.round_id,
                result_json=document,
                completed_at=room.updated_at,
            )
            .on_conflict_do_update(
                index_elements=[CompletedRoomRow.code],
                set_={
                    "graph_version": room.graph_version,
                    "round_id": room.round_id,
                    "result_json": document,
                    "completed_at": room.updated_at,
                },
            )
        )
        async with self._database.session() as session:
            await session.execute(statement)
