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
    'content'           : '',
}


def onsignal_usr1(a, b):
    penv['is_running'] = False


class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, file_path):
        self.rc = penv['rc'][0]
        self.file_path = file_path
        self.last_modified = os.path.getmtime(file_path)

    def on_modified(self, event):
        if event.src_path == self.file_path:
            current_modified = os.path.getmtime(self.file_path)
            if current_modified > self.last_modified:
                self.last_modified = current_modified
                with open(penv['watch_file'], 'r') as f:
                    new_content = f.read()
                diff_content = new_content[len(penv['content']) :]
                penv['content'] = new_content
                self.rc.lpush(penv['emit_key'], diff_content)
                print(f"File {self.file_path} has been modified.")

    def on_created(self, event):
        if event.src_path == self.file_path:
            current_modified = os.path.getmtime(self.file_path)
            if current_modified > self.last_modified:
                self.last_modified = current_modified
                self.rc.delete(penv['emit_key'])
                penv['content'] = ''
                print(f"File {self.file_path} has been created.")


def main():
    signal(SIGUSR1, onsignal_usr1)

    rcp = redis.ConnectionPool(host='localhost', port=5168, password=None, max_connections=15)
    rcc = redis.Redis(connection_pool = rcp)
    if not rcc.ping():
        raise Exception('Redis PING操作异常！')
    penv['rc'] = [rcc, rcp]

    while penv['is_running']:
        if os.path.exists(penv['watch_file']):
            event_handler = FileChangeHandler(penv['watch_file'])
            observer = Observer()
            observer.schedule(event_handler, os.path.dirname(penv['watch_file']), recursive=False)
            observer.start()
            break
        else:
            print(f"File {penv['watch_file']} not exist yet.")
            time.sleep(1.5)

    try:
        while penv['is_running']:
            time.sleep(0.5)
    except (Exception) as e:
        print("发生异常【{}】\n".format(exinfo()))
    finally:
        observer.stop()
        observer.join()
        penv['rc'][0].save()
        penv['rc'][0].close()
        penv['rc'][1].disconnect(inuse_connections=True)


if __name__ == "__main__":
    main()
