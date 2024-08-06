#!/usr/bin/env python3
#coding=utf-8

"""
    Created on: 2024-07-15 by AndyZhou
"""

import os, time, redis, re
from andylog import Andylog
from andyutil import Util
from datetime import datetime
from signal import (signal, SIGUSR1)
from traceback import format_exc as exinfo
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


penv = {
    'andylog'           : Andylog(),
    'is_running'        : True,
    'watch_file'        : [
                            '/home/andy/myae/logs/andygood.log',
                            '/home/andy/myae/logs/trans.log',
                            '/home/andy/myae/logs/qemu.log',
                          ],
    'emit_key'          : 'eng-emit-msg',
    'filter_set'        : set(),
    'pattern'           : re.compile(r".\s{0,3}\d{1,3}\.\d{5,8}.|firmadyne:"),
    'msg_len_valve'     : 100000,
    'watch_qemu_log'    : True,
}


def onsignal_usr1(a, b):
    penv['is_running'] = False


def onsignal_usr2(a, b):
    penv['watch_qemu_log'] = not penv['watch_qemu_log']


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
                for i in new_content:
                    self.rc.rpush(self.key, i)
                    print(f"{self.file_path} modified and diff=> {i}")

    def on_created(self, event):
        if self.__is_self_event(event):
            self.__rst_watch_file()
            print(f"{self.file_path} created once more")

    def on_deleted(self, event):
        if self.__is_self_event(event):
            self.__rst_watch_file()
            print(f"{self.file_path} deleted once more")

    def __diff_watch_file(self):
        new_content = []
        with open(self.file_path, 'rb') as f:
            f.seek(0, os.SEEK_END)
            cur_pos = f.tell()
            if cur_pos <= self.pre_pos:
                self.pre_pos = 0
            if cur_pos > 0:
                read_cnt = cur_pos - self.pre_pos
                f.seek(self.pre_pos, os.SEEK_SET)
                new_content += [f.read(read_cnt).decode('utf8')]
                self.pre_pos = cur_pos

        if self.file_path.rfind('qemu.log') != -1 and penv['watch_qemu_log']:
            if new_content:
                filter_set = penv['filter_set']
                new_content, tmp0 = [], []
                with open(self.file_path) as f:
                    for i in f.readlines():
                        tmp0 += [i[:-2]]
                if len(filter_set) <= 0:
                    tmp2 = len(tmp0)
                    tmp1 = False
                    for i in range(tmp2):
                        if "busybox" in tmp0[i].lower():
                            tmp1 = True
                            tmp2 = i
                            break
                    tmp0 = tmp0[tmp2:] if tmp1 else []
                if tmp0:
                    for i in tmp0:
                        tmp1 = re.split(penv['pattern'], i)
                        tmp1 = ''.join([tmp2.strip() for tmp2 in tmp1])
                        tmp2 = Util.gen_sha1(tmp1.encode('utf8'))
                        if tmp2 not in filter_set:
                            new_content += [f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}] {tmp1}"]
                            filter_set.add(tmp2)
                self.__rst_watch_file()
        return new_content

    def __is_self_event(self, event):
        if event.src_path == self.file_path:
            if os.path.exists(self.file_path):
                current_modified = os.path.getmtime(self.file_path)
                if current_modified > self.last_modified:
                    self.last_modified = current_modified
                    return True
        return False

    def __rst_watch_file(self):
        self.pre_pos = 0


def main():
    signal(SIGUSR1, onsignal_usr1)

    rcp = redis.ConnectionPool(host='localhost', port=5168, password=None, max_connections=15)
    rcc = redis.Redis(connection_pool = rcp)
    if not rcc.ping():
        raise Exception('redis PING操作异常！')
    penv['rc'] = [rcc, rcp]

    observer = Observer(timeout = 0.5)
    for fn in penv['watch_file']:
        if not os.path.exists(fn):
            with open(fn, 'x') as f:
                print(f"touched [{fn}] successfully")
        event_handler = FileChangeHandler(fn)
        observer.schedule(event_handler, os.path.abspath(fn), recursive=False)
    observer.start()
    print(f"watch beginning=> {penv['watch_file']}")

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
        rcc.delete(penv['emit_key'])
        rcc.save()
        rcc.close()
        rcp.disconnect(inuse_connections=True)


if __name__ == "__main__":
    main()
