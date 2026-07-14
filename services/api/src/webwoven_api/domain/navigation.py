"""Pure navigation-stack and immutable-trail behavior."""

from dataclasses import dataclass

from webwoven_api.domain.errors import DomainError


@dataclass(frozen=True, slots=True)
class NavigationState:
    stack: tuple[str, ...]
    trail: tuple[str, ...]
    moves: int

    def __post_init__(self) -> None:
        if not self.stack:
            raise ValueError("navigation stack cannot be empty")
        if len(set(self.stack)) != len(self.stack):
            raise ValueError("navigation stack must contain unique entities")
        if not self.trail:
            raise ValueError("navigation trail cannot be empty")
        if self.trail[-1] != self.stack[-1]:
            raise ValueError("navigation trail and stack must end at the current entity")
        if self.moves < 0:
            raise ValueError("navigation moves cannot be negative")
        if self.moves != len(self.trail) - 1:
            raise ValueError("navigation moves must equal the number of trail transitions")

    @property
    def current_id(self) -> str:
        return self.stack[-1]

    @property
    def active_route_ids(self) -> frozenset[str]:
        """Return entities that cannot be followed without creating a cycle."""
        return frozenset(self.stack)


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
    if edge_target_id in state.active_route_ids:
        raise DomainError(
            "entity_already_in_route",
            "That entity is already in your active route. Use Back to retrace your path.",
        )
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
