"""Stable Valkey key namespace owned by production persistence."""


class ValkeyKeys:
    @staticmethod
    def room(code: str) -> str:
        return f"webwoven:room:{code}"

    @staticmethod
    def room_lock(code: str) -> str:
        return f"webwoven:lock:room:{code}"

    @staticmethod
    def room_events(code: str) -> str:
        return f"webwoven:room:{code}:events"

    @staticmethod
    def room_channel(code: str) -> str:
        return f"webwoven:room:{code}:updates"

    @staticmethod
    def session_room(session_id: str) -> str:
        return f"webwoven:session:{session_id}:room"

    @staticmethod
    def rate_limit(scope: str, identity: str, bucket: int) -> str:
        return f"webwoven:rate:{scope}:{identity}:{bucket}"

    @staticmethod
    def concurrent_limit(scope: str, identity: str) -> str:
        return f"webwoven:concurrent:{scope}:{identity}"
