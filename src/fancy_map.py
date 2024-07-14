from collections.abc import Hashable
from typing import Iterator, Self

from simple_map import SimpleHashmap, _SimpleRecord


class _FancyRecord[_KeyType: Hashable, _ValueType](_SimpleRecord[_KeyType, _ValueType]):
    next_ordered: Self | None
    prev_ordered: Self | None

    def __init__(self, key: _KeyType, value: _ValueType) -> None:
        super().__init__(key, value)
        self.next_ordered = None
        self.prev_ordered = None


class FancyHashmap[_KeyType: Hashable, _ValueType](SimpleHashmap[_KeyType, _ValueType]):
    _head: _FancyRecord[_KeyType, _ValueType] | None
    _tail: _FancyRecord[_KeyType, _ValueType] | None
    # FIXME: Safely make _map covariant

    def __init__(self, size: int | None = None) -> None:
        super().__init__(size or 512)
        self._head = None
        self._tail = None

    def __setitem__(self, key: _KeyType, value: _ValueType) -> None:
        rec, p = self._find(key)

        if rec is not None:
            rec.value = value
            return

        assert isinstance(p, int)

        node = _FancyRecord[_KeyType, _ValueType](key, value)
        m = self._map[p]
        if m is not None and not isinstance(m, _FancyRecord):
            raise TypeError
        node.next_collision = m
        self._map[p] = node

        if self._tail is None:
            assert self._head is None
            self._head = node
        else:
            assert self._tail.next_ordered is None
            self._tail.next_ordered = node
        node.prev_ordered = self._tail
        self._tail = node

        self._count += 1

    def __delitem__(self, key: _KeyType) -> None:
        rec, p = self._find(key)
        if rec is None:
            # Should we error or return?
            return
        if isinstance(p, _SimpleRecord):
            p.next_collision = rec.next_collision
        else:
            self._map[p] = rec.next_collision

        if rec.next_ordered is None:
            assert self._tail is rec
            self._tail = rec.prev_ordered
        else:
            assert rec.next_ordered.prev_ordered is rec
            rec.next_ordered.prev_ordered = rec.prev_ordered
        if rec.prev_ordered is None:
            assert self._head is rec
            self._head = rec.next_ordered
        else:
            assert rec.prev_ordered.next_ordered is rec
            rec.prev_ordered.next_ordered = rec.next_ordered

        self._count -= 1

    def __iter__(self) -> Iterator[_KeyType]:
        node = self._head
        while node is not None:
            yield node.key
            node = node.next_ordered

    def _find(
        self, key: _KeyType
    ) -> tuple[
        _FancyRecord[_KeyType, _ValueType] | None,
        _FancyRecord[_KeyType, _ValueType] | int,
    ]:
        a, b = super()._find(key)
        if a is not None and not isinstance(a, _FancyRecord):
            raise TypeError
        if not isinstance(b, (_FancyRecord, int)):
            raise TypeError
        return (a, b)
