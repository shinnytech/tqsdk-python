#!usr/bin/env python3
#-*- coding:utf-8 -*-
__author__ = 'yanqiong'

import copy
import weakref
from collections.abc import MutableMapping

_UNSET = object()


class Entity(MutableMapping):
    __slots__ = ('_data', '_path', '_listener', '__dict__')

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        object.__setattr__(instance, '_data', {})
        return instance

    def _instance_entity(self, path):
        object.__setattr__(self, '_path', path)
        object.__setattr__(self, '_listener', None)

    def __setattr__(self, key, value):
        if key.startswith('_'):
            object.__setattr__(self, key, value)
        else:
            self._data[key] = value

    def __getattr__(self, key):
        try:
            return self._data[key]
        except KeyError:
            raise AttributeError(key)

    def _add_listener(self, chan):
        """Add a listener, lazily creating the WeakSet if needed."""
        listener = self._listener
        if listener is None:
            listener = weakref.WeakSet()
            object.__setattr__(self, '_listener', listener)
        listener.add(chan)

    def __delattr__(self, key):
        if key.startswith('_'):
            object.__delattr__(self, key)
        else:
            try:
                del self._data[key]
            except KeyError:
                raise AttributeError(key)

    def __setitem__(self, key, value):
        self._data[key] = value

    def __delitem__(self, key):
        del self._data[key]

    def __getitem__(self, key):
        return self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __str__(self):
        return str(self._data)

    def __repr__(self):
        return '{}, D({})'.format(super(Entity, self).__repr__(), self._data)

    def __contains__(self, key):
        return key in self._data

    def get(self, key, default=None):
        return self._data.get(key, default)

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def items(self):
        return self._data.items()

    def pop(self, key, *args):
        return self._data.pop(key, *args)

    def setdefault(self, key, default=None):
        return self._data.setdefault(key, default)

    def __copy__(self):
        new = type(self).__new__(type(self))
        # Copy slot attrs using getattr to avoid exception overhead for unset slots
        _setattr = object.__setattr__
        _p = getattr(self, '_path', _UNSET)
        if _p is not _UNSET:
            _setattr(new, '_path', _p)
        _l = getattr(self, '_listener', _UNSET)
        if _l is not _UNSET:
            _setattr(new, '_listener', _l)
        # Copy any extra attrs from __dict__
        d = self.__dict__
        if d:
            for k, v in d.items():
                _setattr(new, k, v)
        _setattr(new, '_data', self._data.copy())
        return new

    def copy(self):
        return copy.copy(self)
