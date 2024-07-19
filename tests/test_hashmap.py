from itertools import pairwise

import fancy_map as fm
import pytest
import simple_map as sm


def test_simple_record_init():
    key = "This is a key!"
    value = "This is a value!"
    rec = sm._SimpleRecord(key, value)

    assert rec.key is key
    assert rec.value is value
    assert rec.next_collision is None


def test_simple_record_find():
    key = "This is a key!"
    value = "This is a value!"
    rec_1 = sm._SimpleRecord(key, value)

    res = rec_1.find("Hello!")
    assert res is None
    res = rec_1.find(key)
    assert res == (rec_1, None)

    rec_2 = sm._SimpleRecord(value, key)
    rec_1.next_collision = rec_2

    res = rec_1.find("Hello!")
    assert res is None
    res = rec_1.find(key)
    assert res == (rec_1, None)
    res = rec_1.find(value)
    assert res == (rec_2, rec_1)


def t_hashmap(m: sm.SimpleHashmap[str, str]):
    test_data = list(pairwise("abcdefghijklmnopqrstuvwxyz"))

    assert m._count == 0
    assert m._map == [None, None, None, None, None]

    for i, v in test_data:
        m[i] = v

    assert len(m) == 25
    li = list(m)
    assert len(li) == 25

    for i, v in test_data:
        assert m[i] == v
        assert i in li
    if isinstance(m, fm.FancyHashmap):
        assert li == [x[0] for x in test_data]

    m["y"] = "a"
    assert m["y"] == "a"
    assert len(m) == 25
    m["y"] = "z"

    for i, _ in test_data[:5]:
        del m[i]
    assert len(m) == 20
    for i, _ in test_data[:5]:
        with pytest.raises(KeyError):
            v = m[i]
        with pytest.raises(KeyError):
            del m[i]
    for i, v in test_data[5:]:
        assert m[i] == v

    for i, _ in test_data[5:]:
        del m[i]
    assert len(m) == 0
    assert m._map == [None, None, None, None, None]


def test_simple_hashmap():
    t_hashmap(sm.SimpleHashmap[str, str](5))


def test_fancy_hashmap():
    t_hashmap(fm.FancyHashmap(5))
