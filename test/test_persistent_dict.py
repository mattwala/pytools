from __future__ import division, with_statement, absolute_import

import pytest  # noqa
import sys  # noqa
import tempfile
import shutil
import warnings

from six.moves import range
from six.moves import zip

from pytools.persistent_dict import (PersistentDict,
                                     WriteOncePersistentDict,
                                     NoSuchEntryError,
                                     ReadOnlyEntryError)


# {{{ type for testing

class PDictTestingKeyOrValue(object):

    def __init__(self, val, hash_key=None):
        self.val = val
        if hash_key is None:
            hash_key = val
        self.hash_key = hash_key

    def __getstate__(self):
        return {"val": self.val, "hash_key": self.hash_key}

    def __eq__(self, other):
        return self.val == other.val

    def __ne__(self, other):
        return not self.__eq__(other)

    def update_persistent_hash(self, key_hash, key_builder):
        key_builder.rec(key_hash, self.hash_key)

# }}}


def test_persistent_dict_storage_and_lookup():
    try:
        tmpdir = tempfile.mkdtemp()
        pdict = PersistentDict(tmpdir)

        from random import randrange

        def rand_str(n=20):
            return "".join(
                    chr(65+randrange(26))
                    for i in range(n))

        keys = [(randrange(2000), rand_str(), None) for i in range(20)]
        values = [randrange(2000) for i in range(20)]

        d = dict(list(zip(keys, values)))

        # {{{ check lookup

        for k, v in zip(keys, values):
            pdict[k] = v

        for k, v in d.items():
            assert d[k] == pdict[k]

        # }}}

        # {{{ check updating

        for k, v in zip(keys, values):
            pdict[k] = v + 1

        for k, v in d.items():
            assert d[k] + 1 == pdict[k]

        # }}}

        # {{{ check not found

        with pytest.raises(NoSuchEntryError):
            pdict[3000]

        # }}}

    finally:
        shutil.rmtree(tmpdir)


def test_persistent_dict_deletion():
    try:
        tmpdir = tempfile.mkdtemp()
        pdict = PersistentDict(tmpdir)

        pdict[0] = 0
        del pdict[0]

        with pytest.raises(NoSuchEntryError):
            pdict[0]

        with pytest.raises(NoSuchEntryError):
            del pdict[1]

    finally:
        shutil.rmtree(tmpdir)


def test_persistent_dict_synchronization():
    try:
        tmpdir = tempfile.mkdtemp()
        pdict1 = PersistentDict(tmpdir)
        pdict2 = PersistentDict(tmpdir)

        # check lookup
        pdict1[0] = 1
        assert pdict2[0] == 1

        # check updating
        pdict1[0] = 2
        assert pdict2[0] == 2

        # check deletion
        del pdict1[0]
        with pytest.raises(NoSuchEntryError):
            pdict2[0]

    finally:
        shutil.rmtree(tmpdir)


def test_persistent_dict_cache_collisions():
    try:
        tmpdir = tempfile.mkdtemp()
        pdict = PersistentDict(tmpdir)

        key1 = PDictTestingKeyOrValue(1, hash_key=0)
        key2 = PDictTestingKeyOrValue(2, hash_key=0)

        pdict[key1] = 1

        # Suppress pdict collision warnings.
        with warnings.catch_warnings():
            # check lookup
            with pytest.raises(NoSuchEntryError):
                pdict[key2]

            # check deletion
            with pytest.raises(NoSuchEntryError):
                del pdict[key2]

    finally:
        shutil.rmtree(tmpdir)


def test_write_once_persistent_dict_storage_and_lookup():
    try:
        tmpdir = tempfile.mkdtemp()
        pdict = WriteOncePersistentDict(tmpdir)

        # check lookup
        pdict[0] = 1
        assert pdict[0] == 1

        # check updating
        with pytest.raises(ReadOnlyEntryError):
            pdict[0] = 2

    finally:
        shutil.rmtree(tmpdir)


def test_write_once_persistent_dict_lru_policy():
    try:
        tmpdir = tempfile.mkdtemp()
        pdict = WriteOncePersistentDict(tmpdir, in_mem_cache_size=3)

        pdict[1] = PDictTestingKeyOrValue(1)
        pdict[2] = PDictTestingKeyOrValue(2)
        pdict[3] = PDictTestingKeyOrValue(3)
        pdict[4] = PDictTestingKeyOrValue(4)

        val1 = pdict[1]

        assert pdict[1] is val1
        pdict[2]
        assert pdict[1] is val1
        pdict[3]
        assert pdict[1] is val1
        pdict[2]
        assert pdict[1] is val1
        pdict[4]
        assert pdict[1] is not val1

    finally:
        shutil.rmtree(tmpdir)


def test_write_once_persistent_dict_synchronization():
    try:
        tmpdir = tempfile.mkdtemp()
        pdict1 = WriteOncePersistentDict(tmpdir)
        pdict2 = WriteOncePersistentDict(tmpdir)

        # check lookup
        pdict1[1] = 0
        assert pdict2[1] == 0

        # check updating
        with pytest.raises(ReadOnlyEntryError):
            pdict2[1] = 1

    finally:
        shutil.rmtree(tmpdir)


def test_write_once_persistent_dict_cache_collisions():
    try:
        tmpdir = tempfile.mkdtemp()
        pdict = WriteOncePersistentDict(tmpdir)

        key1 = PDictTestingKeyOrValue(1, hash_key=0)
        key2 = PDictTestingKeyOrValue(2, hash_key=0)

        pdict[key1] = 1

        # Suppress pdict collision warnings.
        with warnings.catch_warnings():
            # check lookup
            with pytest.raises(NoSuchEntryError):
                pdict[key2]

    finally:
        shutil.rmtree(tmpdir)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        exec(sys.argv[1])
    else:
        from py.test.cmdline import main
        main([__file__])
