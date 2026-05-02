"""Binary space partitioning generator for galaxy sectors."""

from __future__ import annotations

from dataclasses import dataclass, field
import random
from typing import Protocol


class RandomLike(Protocol):
    """Subset of random.Random used by the BSP generator."""

    def randint(self, a: int, b: int) -> int:
        """Return a random integer in the inclusive range."""

    def random(self) -> float:
        """Return a float in the half-open range [0.0, 1.0)."""


@dataclass(frozen=True)
class Rect:
    """Integer rectangle used by BSP leaves and rooms."""

    x: int
    y: int
    width: int
    height: int

    @property
    def center(self) -> tuple[int, int]:
        """Return the center point of the rectangle."""

        return (self.x + self.width // 2, self.y + self.height // 2)


@dataclass
class BspNode:
    """A node in a binary space partitioning tree."""

    bounds: Rect
    depth: int = 0
    left: BspNode | None = None
    right: BspNode | None = None
    room: Rect | None = None
    corridors: list[tuple[tuple[int, int], tuple[int, int]]] = field(
        default_factory=list
    )

    @property
    def is_leaf(self) -> bool:
        """Return True when the node has no children."""

        return self.left is None and self.right is None


class BspGenerator:
    """Generate rooms and corridors by recursively splitting a rectangle."""

    def __init__(
        self,
        width: int,
        height: int,
        min_leaf_size: int,
        max_depth: int,
        seed: int | None = None,
    ) -> None:
        """Initialize the generator.

        Args:
            width: Width of the generated field.
            height: Height of the generated field.
            min_leaf_size: Minimum allowed leaf dimension.
            max_depth: Maximum recursion depth.
            seed: Optional deterministic seed.

        Raises:
            ValueError: If dimensions are too small.
        """

        if width < min_leaf_size * 2 or height < min_leaf_size * 2:
            msg = "BSP field must fit at least two leaves in each dimension"
            raise ValueError(msg)
        self._width = width
        self._height = height
        self._min_leaf_size = min_leaf_size
        self._max_depth = max_depth
        self._random: RandomLike = random.Random(seed)

    def generate(self) -> tuple[BspNode, list[Rect], list[tuple[int, int]]]:
        """Build the tree and return its root, rooms, and corridor edges."""

        root = BspNode(Rect(0, 0, self._width, self._height))
        self._split(root)
        rooms = self._create_rooms(root)
        corridors = self._collect_corridors(root)
        return root, rooms, corridors

    def _split(self, node: BspNode) -> None:
        if node.depth >= self._max_depth:
            return

        can_split_h = node.bounds.height >= self._min_leaf_size * 2
        can_split_v = node.bounds.width >= self._min_leaf_size * 2
        if not can_split_h and not can_split_v:
            return

        split_vertical = self._choose_split_axis(node.bounds, can_split_h, can_split_v)
        if split_vertical:
            split_at = self._random.randint(
                self._min_leaf_size, node.bounds.width - self._min_leaf_size
            )
            left_bounds = Rect(
                node.bounds.x, node.bounds.y, split_at, node.bounds.height
            )
            right_bounds = Rect(
                node.bounds.x + split_at,
                node.bounds.y,
                node.bounds.width - split_at,
                node.bounds.height,
            )
        else:
            split_at = self._random.randint(
                self._min_leaf_size, node.bounds.height - self._min_leaf_size
            )
            left_bounds = Rect(
                node.bounds.x, node.bounds.y, node.bounds.width, split_at
            )
            right_bounds = Rect(
                node.bounds.x,
                node.bounds.y + split_at,
                node.bounds.width,
                node.bounds.height - split_at,
            )

        node.left = BspNode(left_bounds, node.depth + 1)
        node.right = BspNode(right_bounds, node.depth + 1)
        self._split(node.left)
        self._split(node.right)

    def _choose_split_axis(
        self, bounds: Rect, can_split_h: bool, can_split_v: bool
    ) -> bool:
        if not can_split_h:
            return True
        if not can_split_v:
            return False
        if bounds.width > bounds.height * 1.25:
            return True
        if bounds.height > bounds.width * 1.25:
            return False
        return self._random.random() < 0.5

    def _create_rooms(self, node: BspNode) -> list[Rect]:
        if node.is_leaf:
            margin = max(2, self._min_leaf_size // 5)
            room_width = self._random.randint(
                max(4, node.bounds.width // 3), max(5, node.bounds.width - margin)
            )
            room_height = self._random.randint(
                max(4, node.bounds.height // 3), max(5, node.bounds.height - margin)
            )
            room_x = node.bounds.x + self._random.randint(
                1, max(1, node.bounds.width - room_width)
            )
            room_y = node.bounds.y + self._random.randint(
                1, max(1, node.bounds.height - room_height)
            )
            node.room = Rect(room_x, room_y, room_width, room_height)
            return [node.room]

        rooms: list[Rect] = []
        if node.left is not None:
            rooms.extend(self._create_rooms(node.left))
        if node.right is not None:
            rooms.extend(self._create_rooms(node.right))

        left_room = self._first_room(node.left)
        right_room = self._first_room(node.right)
        if left_room is not None and right_room is not None:
            node.corridors.append((left_room.center, right_room.center))
        return rooms

    def _first_room(self, node: BspNode | None) -> Rect | None:
        if node is None:
            return None
        if node.room is not None:
            return node.room
        return self._first_room(node.left) or self._first_room(node.right)

    def _collect_corridors(
        self, node: BspNode
    ) -> list[tuple[tuple[int, int], tuple[int, int]]]:
        corridors = list(node.corridors)
        if node.left is not None:
            corridors.extend(self._collect_corridors(node.left))
        if node.right is not None:
            corridors.extend(self._collect_corridors(node.right))
        return corridors
