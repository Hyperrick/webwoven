"""Pure navigation-stack and immutable-trail behavior."""

from dataclasses import dataclass

from webwoven_api.domain.errors import DomainError


@dataclass(frozen=True, slots=True)
class NavigationState:
    stack: tuple[str, ...]
    trail: tuple[str, ...]
    moves: int

    @property
    def current_id(self) -> str:
        return self.stack[-1]


def start_navigation(entity_id: str) -> NavigationState:
    if not entity_id:
        raise ValueError("entity_id is required")
    return NavigationState(stack=(entity_id,), trail=(entity_id,), moves=0)


def follow_edge(
    state: NavigationState,
    *,
    edge_source_id: str,
    edge_target_id: str,
) -> NavigationState:
    """Follow an edge from the current node and append it to both histories."""
    if edge_source_id != state.current_id:
        raise DomainError("edge_source_mismatch", "That route no longer starts here.")
    return NavigationState(
        stack=(*state.stack, edge_target_id),
        trail=(*state.trail, edge_target_id),
        moves=state.moves + 1,
    )


def go_back(state: NavigationState) -> NavigationState:
    """Pop navigation while retaining the revisit in the visible trail."""
    if len(state.stack) == 1:
        raise DomainError("already_at_start", "You are already at the start of this route.")
    stack = state.stack[:-1]
    return NavigationState(
        stack=stack,
        trail=(*state.trail, stack[-1]),
        moves=state.moves + 1,
    )
