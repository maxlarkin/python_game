"""Recursive QuadTree spatial index."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, TypeVar


class HasBounds(Protocol):
    """Protocol for objects that can be indexed by QuadTree."""

    def bounds(self) -> Rect:
        """Return object bounds."""


@dataclass(frozen=True)
class Rect:
    """Axis-aligned rectangle."""

    x: float
    y: float
    width: float
    height: float

    @property
    def right(self) -> float:
        """Return the right edge."""

        return self.x + self.width

    @property
    def bottom(self) -> float:
        """Return the bottom edge."""

        return self.y + self.height

    def contains(self, other: Rect) -> bool:
        """Return True when this rectangle fully contains another."""

        return (
            self.x <= other.x
            and self.y <= other.y
            and self.right >= other.right
            and self.bottom >= other.bottom
        )

    def intersects(self, other: Rect) -> bool:
        """Return True when rectangles overlap."""

        return not (
            other.x > self.right
            or other.right < self.x
            or other.y > self.bottom
            or other.bottom < self.y
        )


T = TypeVar("T", bound=HasBounds)


class QuadTree[T]:
    """Spatial index that recursively subdivides crowded regions."""

    def __init__(
        self,
        boundary: Rect,
        capacity: int,
        max_depth: int,
        depth: int = 0,
    ) -> None:
        """Initialize an empty tree.

        Args:
            boundary: Region covered by this tree node.
            capacity: Number of objects stored before subdivision.
            max_depth: Maximum subdivision depth.
            depth: Current depth, used internally.
        """

        self._boundary = boundary
        self._capacity = capacity
        self._max_depth = max_depth
        self._depth = depth
        self._objects: list[T] = []
        self._children: list[QuadTree[T]] = []

    def clear(self) -> None:
        """Remove all indexed objects."""

        self._objects.clear()
        self._children.clear()

    def insert(self, obj: T) -> bool:
        """Insert an object and return whether it fits inside this tree."""

        obj_bounds = obj.bounds()
        if not self._boundary.intersects(obj_bounds):
            return False

        if self._children:
            child = self._child_containing(obj_bounds)
            if child is not None:
                return child.insert(obj)

        self._objects.append(obj)
        if (
            len(self._objects) > self._capacity
            and self._depth < self._max_depth
            and not self._children
        ):
            self._subdivide()
        return True

    def query(self, area: Rect) -> list[T]:
        """Return all objects whose bounds intersect an area."""

        found: list[T] = []
        self.query_into(area, found)
        return found

    def query_into(self, area: Rect, found: list[T]) -> None:
        """Append matching objects to an existing list."""

        if not self._boundary.intersects(area):
            return

        for obj in self._objects:
            if obj.bounds().intersects(area):
                found.append(obj)

        for child in self._children:
            child.query_into(area, found)

    def _subdivide(self) -> None:
        half_width = self._boundary.width / 2.0
        half_height = self._boundary.height / 2.0
        x = self._boundary.x
        y = self._boundary.y
        children = [
            Rect(x, y, half_width, half_height),
            Rect(x + half_width, y, half_width, half_height),
            Rect(x, y + half_height, half_width, half_height),
            Rect(x + half_width, y + half_height, half_width, half_height),
        ]
        self._children = [
            QuadTree(child, self._capacity, self._max_depth, self._depth + 1)
            for child in children
        ]

        kept: list[T] = []
        for obj in self._objects:
            child = self._child_containing(obj.bounds())
            if child is None:
                kept.append(obj)
            else:
                child.insert(obj)
        self._objects = kept

    def _child_containing(self, bounds: Rect) -> QuadTree[T] | None:
        for child in self._children:
            if child._boundary.contains(bounds):
                return child
        return None
