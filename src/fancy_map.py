import weakref
from collections.abc import Hashable, Iterator, Reversible
from copy import deepcopy
from numbers import Real
from typing import Literal, Self, SupportsIndex

from simple_map import SimpleHashmap, _SimpleRecord


class _FancyRecord[_KeyType: Hashable, _ValueType](_SimpleRecord[_KeyType, _ValueType]):
    next_ordered: Self | None
    prev_ordered: Self | None
    l_index: int | None

    def __init__(self, key: _KeyType, value: _ValueType) -> None:
        super().__init__(key, value)
        self.next_ordered = None
        self.prev_ordered = None


class FancyHashmap[_KeyType: Hashable, _ValueType](
    SimpleHashmap[_KeyType, _ValueType], Reversible[_KeyType]
):
    highwater: float | Real | None | Literal[False]
    lowwater: float | Real | None

    _head: _FancyRecord[_KeyType, _ValueType] | None
    _tail: _FancyRecord[_KeyType, _ValueType] | None
    _array: list[weakref.ref[_FancyRecord[_KeyType, _ValueType]]]
    # FIXME: Safely make _map covariant

    def __init__(self, size: int | None = None) -> None:
        super().__init__(size or 512)
        self._head = None
        self._tail = None
        self._array = []

        self.highwater = 0.9
        # low

    def copy_with_size(self, size: int | None = None) -> None:
        if size is None:
            size = (
                2 << self._count.bit_length()
            )  # The two there instead of one is intentional
        if size <= 0:
            raise ValueError

    def resize(self, size: int | None = None) -> None:
        if size is None:
            size = (
                2 << self._count.bit_length()
            )  # The two there instead of one is intentional
        if size <= 0:
            raise ValueError

        it = self._iter_f()
        self._map = [None] * size
        for node in it:
            rec, p = self._find(node.key)
            assert rec is None and isinstance(p, int)  # The item shouldn't be there yet

            # Add to hashmap
            m = self._map[p]
            if m is not None and not isinstance(m, _FancyRecord):
                raise TypeError
            node.next_collision = m
            self._map[p] = node

    def iat(self, index: SupportsIndex) -> tuple[_KeyType, _ValueType]:
        """Select a key value pair from a given integer.

        For speed, this gets an entry from an internal list.
        However, that list is not guaranteed to be in any particular
        order, and can change arbitrily whenever an entry is added to
        or removed from the mapping.

        If the order of items matter, use the `iter` function instead."""
        rec = self._by_index(index)
        return (rec.key, rec.value)

    def __contains__(self, key: object) -> bool:
        if not isinstance(key, Hashable):
            return False
        return bool(self._find(key)[0])

    def __setitem__(self, key: _KeyType, value: _ValueType) -> None:
        rec, p = self._find(key)

        if rec is not None:
            rec.value = value
            return

        assert isinstance(p, int)

        # Add to hashmap
        node = _FancyRecord[_KeyType, _ValueType](key, value)
        m = self._map[p]
        if m is not None and not isinstance(m, _FancyRecord):
            raise TypeError
        node.next_collision = m
        self._map[p] = node

        # Add to linked list
        if self._tail is None:
            assert self._head is None
            self._head = node
        else:
            assert self._tail.next_ordered is None
            self._tail.next_ordered = node
        node.prev_ordered = self._tail
        self._tail = node

        # Add to array
        self._array.append(weakref.ref(node))
        node.l_index = self._count

        self._count += 1

    def __delitem__(self, key: _KeyType) -> None:
        rec, p = self._find(key)
        if rec is None:
            raise KeyError

        # Remove from hashmap
        if isinstance(p, _SimpleRecord):
            p.next_collision = rec.next_collision
        else:
            self._map[p] = rec.next_collision

        # Remove from linked list
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

        # Remove from array
        a = self._array  # just to save letters
        i = rec.l_index
        assert isinstance(i, int)
        a[-1], a[i] = a[i], a[-1]
        a.pop()

        self._count -= 1

    def clear(self) -> None:
        self._map.clear()
        self._array.clear()
        self._count = 0
        self._head = None
        self._tail = None

    def popitem(self, last: bool = True) -> tuple[_KeyType, _ValueType]:
        # Uses same signature as OrderedDict
        if self._count <= 0:
            raise KeyError

        if last:
            rec = self._tail
        else:
            rec = self._head
        assert rec is not None
        key, value = rec.key, rec.value

        del self[key]
        return (key, value)

    def __iter__(self) -> Iterator[_KeyType]:
        return (x.key for x in self._iter_f())

    def __reversed__(self) -> Iterator[_KeyType]:
        return (x.key for x in self._iter_r())

    def __deepcopy__(self, memo) -> Self:
        new = object.__new__(type(self))
        memo[id(self)] = new
        new.__dict__.update(deepcopy(self.__dict__, memo))

        new_arr = []
        node = new._head
        i = 0
        while node is not None:
            new_arr.append(weakref.ref(node))
            node.l_index = i
            node = node.next_ordered
            i += 1

        new._array = new_arr
        return new

    def _iter_f(self) -> Iterator[_FancyRecord[_KeyType, _ValueType]]:
        node = self._head
        while node is not None:
            yield node
            node = node.next_ordered

    def _iter_r(self) -> Iterator[_FancyRecord[_KeyType, _ValueType]]:
        node = self._tail
        while node is not None:
            yield node
            node = node.prev_ordered

    def _find(
        self, key: Hashable
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

    def _by_index(self, index: SupportsIndex) -> _FancyRecord[_KeyType, _ValueType]:
        rec = self._array[index]()
        if rec is None:
            raise ReferenceError
        return rec
