#!usr/bin/env python3
#-*- coding:utf-8 -*-
__author__ = 'yanqiong'

import copy
import weakref
from collections.abc import MutableMapping


class Entity(MutableMapping):
    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        object.__setattr__(instance, '_data', {})
        return instance

    def _instance_entity(self, path):
        object.__setattr__(self, '_path', path)
        object.__setattr__(self, '_listener', weakref.WeakSet())

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

    def __copy__(self):
        new = type(self).__new__(type(self))
        # Copy private attrs from __dict__ (excluding _data which is handled separately)
        for k, v in self.__dict__.items():
            if k != '_data':
                object.__setattr__(new, k, v)
        object.__setattr__(new, '_data', self._data.copy())
        return new

    def copy(self):
        return copy.copy(self)
