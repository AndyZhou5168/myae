#!/usr/bin/env python3
#coding=utf-8

"""
    Created on: 2023-02-20 by AndyZhou
"""


class Singleton(object):
    def __new__(cls, *args, **kw):
        if not hasattr(cls, '_instance'):
            orig = super(Singleton, cls)
            cls._instance = orig.__new__(cls)
        return cls._instance
