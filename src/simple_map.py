from typing import Self
from collections.abc import Hashable, MutableMapping


class _SimpleRecord[_KeyType: Hashable, _ValueType]:
    key: _KeyType
    value: _ValueType
    next_collision: Self | None

    def __init__(self, key: _KeyType, value: _ValueType) -> None:
        self.key = key
        self.value = value
        self.next_collision = None

    def find(self, key: _KeyType) -> tuple[Self, Self | None] | None:
        """
        Return this object or the first collided node that matches the key.

        The second argument of the tuple is the node that directly links
        to the returned node, or None if self is returned.
        """

        last = None
        record = self

        while record is not None:
            if record.key == key:
                return (record, last)
            last = record
            record = record.next_collision

        return None

    def __str__(self) -> str:
        return f"{self.key} : {self.value} [{self.next_collision}]"


class SimpleHashmap[_KeyType: Hashable, _ValueType](
    MutableMapping[_KeyType, _ValueType]
):
    _map: list[_SimpleRecord[_KeyType, _ValueType] | None]
    _count: int

    def __init__(self, size: int | None = None) -> None:
        if size is None:
            raise TypeError
        if size <= 1:
            raise ValueError

        self._map = [None] * size
        self._count = 0

    def __getitem__(self, key: _KeyType) -> _ValueType:
        rec = self._find(key)
        if rec[0] is None:
            raise KeyError
        return rec[0].value

    def __setitem__(self, key: _KeyType, value: _ValueType) -> None:
        rec = self._find(key)

        if rec[0] is not None:
            rec[0].value = value
            return

        assert isinstance(rec[1], int)

        node = _SimpleRecord[_KeyType, _ValueType](key, value)
        node.next_collision = self._map[rec[1]]
        self._map[rec[1]] = node

        self._count += 1

    def __delitem__(self, key: _KeyType) -> None:
        rec = self._find(key)
        if rec[0] is None:
            # Should we error or return?
            return
        if isinstance(rec[1], _SimpleRecord):
            rec[1].next_collision = rec[0].next_collision
        else:
            self._map[rec[1]] = rec[0].next_collision

        self._count -= 1

    def __len__(self) -> int:
        return self._count

    def _find(
        self, key: _KeyType
    ) -> tuple[
        _SimpleRecord[_KeyType, _ValueType] | None,
        _SimpleRecord[_KeyType, _ValueType] | int,
    ]:
        h = hash(key) % len(self._map)
        rec = self._map[h]
        if rec is None:
            return (None, h)
        res = rec.find(key)
        if res is None:
            return (None, h)
        return (res[0], res[1] or h)
