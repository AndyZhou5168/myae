#!/usr/bin/env python3
#coding=utf-8

"""
    Created on: 2022-05-08 by AndyZhou
"""

import sys, logging, os
from clsbase import Singleton


def andycaller(func):
    def wrapper(*args):
        filename =  sys._getframe(1).f_code.co_filename
        lineno = sys._getframe(1).f_lineno

        args = list(args)
        args.insert(1, f'{os.path.basename(filename)}:{lineno} => ')
        func(*args)
    return wrapper


class Andylog(Singleton):
    def __init__(self, name=''):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('[%(asctime)s] [pid:%(process)d:%(threadName)s] [%(name)s:%(levelname)s]::%(message)s')
        fh = logging.StreamHandler()
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
        import builtins
        builtins.__dict__["print"] = self.info


    @andycaller
    def info(self, *content):
        getattr(self.logger, 'info')(''.join([str(i) for i in content]))


    @andycaller
    def error(self, *content):
        getattr(self.logger, 'error')(''.join([str(i) for i in content]))


    @andycaller
    def debug(self, *content):
        getattr(self.logger, 'debug')(''.join([str(i) for i in content]))


    @andycaller
    def warning(self, *content):
        getattr(self.logger, 'warning')(''.join([str(i) for i in content]))


if __name__ == '__main__':
    pass
