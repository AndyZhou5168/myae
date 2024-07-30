#!/usr/bin/env python3
#coding=utf-8

"""
    Created on: 2024-07-15 by AndyZhou
"""

import os, time, redis
from andylog import Andylog
from signal import (signal, SIGUSR1)
from traceback import format_exc as exinfo
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


penv = {
    'andylog'           : Andylog(),
    'is_running'        : True,
    'watch_file'        : '/home/andy/myae/share/andygood.log',
    'emit_key'          : 'eng-emit-msg',
    'msg_len_valve'     : 100000,
}


def onsignal_usr1(a, b):
    penv['is_running'] = False


class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, file_path):
        self.rc = penv['rc'][0]
        self.key = penv['emit_key']
        self.file_path = file_path
        self.last_modified = os.path.getmtime(file_path)
        self.pre_pos = 0

    def on_modified(self, event):
        if self.__is_self_event(event):
            new_content = self.__diff_watch_file()
            if new_content:
                self.rc.rpush(self.key, new_content)
                print(f"{self.file_path} modified and diff=> {new_content}")

    def on_created(self, event):
        if self.__is_self_event(event):
            self.__rst_watch_file()
            print(f"{penv['watch_file']} created once more")

    def __diff_watch_file(self):
        new_content = None
        with open(self.file_path, 'rb') as f:
            f.seek(0, os.SEEK_END)
            cur_pos = f.tell()
            if cur_pos <= self.pre_pos:
                self.pre_pos = 0
            if cur_pos > 0:
                read_cnt = cur_pos - self.pre_pos
                f.seek(self.pre_pos, os.SEEK_SET)
                new_content = f.read(read_cnt).decode('utf8')
                self.pre_pos = cur_pos
        return new_content

    def __is_self_event(self, event):
        if event.src_path == self.file_path:
            current_modified = os.path.getmtime(self.file_path)
            if current_modified > self.last_modified:
                self.last_modified = current_modified
                return True
        return False

    def __rst_watch_file(self):
        self.rc.delete(self.key)
        self.pre_pos = 0


def main():
    signal(SIGUSR1, onsignal_usr1)

    rcp = redis.ConnectionPool(host='localhost', port=5168, password=None, max_connections=15)
    rcc = redis.Redis(connection_pool = rcp)
    if not rcc.ping():
        raise Exception('redis PING操作异常！')
    penv['rc'] = [rcc, rcp]

    while penv['is_running']:
        if os.path.exists(penv['watch_file']):
            rcc.delete(penv['emit_key'])

            event_handler = FileChangeHandler(penv['watch_file'])
            observer = Observer(timeout = 0.5)
            observer.schedule(event_handler, os.path.dirname(penv['watch_file']), recursive=False)
            observer.start()

            print(f"{penv['watch_file']} has been created")
            break
        else:
            time.sleep(2.0)

    try:
        rdb_cnt = 100
        while penv['is_running']:
            queue_length = rcc.llen(penv['emit_key'])
            if queue_length >= penv['msg_len_valve']:
                rcc.ltrim(penv['emit_key'], queue_length - penv['msg_len_valve'], queue_length)

            rdb_cnt -= 1
            if rdb_cnt < 0:
                rcc.bgsave()
                rdb_cnt = 100

            time.sleep(2.0)

    except (Exception) as e:
        print("发生异常【{}】\n".format(exinfo()))
    finally:
        observer.stop()
        observer.join()
        rcc.save()
        rcc.close()
        rcp.disconnect(inuse_connections=True)


if __name__ == "__main__":
    main()
