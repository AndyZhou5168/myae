#!/usr/bin/env python3
#coding=utf-8

import sys, os.path, subprocess, signal, time
from socket import *

version_info = sys.version_info
if version_info >= (3, 13):
    import telnetlib3 as telnetlib
else:
    import telnetlib


class firmae_helper():
    def __init__(self, iid):
        self.iid = int(iid)
        self.targetName = open('./scratch/%d/name' % iid).read().strip()
        self.targetIP = open('./scratch/%d/ip' % iid).read().strip()
        self.telnetInit = False
        self.netcatOn = False

    def show_info(self):
        print('[*] firmware - %s' % self.targetName)
        print('[*] IP - %s' % self.targetIP)

    def connect(self):
        if not self.netcatOn:
            self.sock = socket(AF_INET, SOCK_STREAM)
            print('[*] connecting to netcat (%s:%d)' % (self.targetIP, 31337))
            try:
                self.sock.connect((self.targetIP, 31337))
            except:
                print('[-] failed to connect netcat')
                return
            self.netcatOn = True
            print('[+] netcat connected')

    def sendrecv(self, cmd):
        self.connect()

        if self.netcatOn:
            self.sock.send(cmd.encode())
            time.sleep(1)
            return self.sock.recv(2048).decode()
        else:
            return ''

    def send(self, cmd):
        self.connect()

        if self.netcatOn:
            self.sock.send(cmd.encode())

    def initalize_telnet(self):
        for command in [
            '/firmadyne/busybox mkdir -p /proc',
            '/firmadyne/busybox ln -sf /proc/mounts /etc/mtab',
            '/firmadyne/busybox mkdir -p /dev/pts',
            '/firmadyne/busybox mount -t devpts devpts /dev/pts',
            ]:
            self.send(command + '\n')
            time.sleep(0.5)
        self.telnetInit = True

    def connect_socat(self):
        argv = ['socat', '-', 'UNIX-CONNECT:/tmp/qemu.' + str(self.iid) + '.S1']
        if os.getuid() != 0:
            argv.insert(0, 'sudo')
        subprocess.call(argv)

    def connect_shell(self):
        self.connect()

        if self.netcatOn:
            if not self.telnetInit:
                self.initalize_telnet()
            subprocess.call(['telnet', self.targetIP, '31338'])

    def show_processlist(self):
        self.pids = self.sendrecv("ps|awk '{print $1}'\n")
        self.pids = self.pids.split('\n')[1:]
        print(self.sendrecv("ps|awk '{print $0}'\n"))

    def tcpdump(self):
        argument = input('sudo tcpdump -i tap%d ' %self.iid)
        os.system('sudo tcpdump -i tap%d %s' %(self.iid, argument))

    def file_transfer(self, target_filepath):
        file_name = os.path.basename(target_filepath)
        self.send(f"/firmadyne/busybox nc -lp 31339 > /opt/{file_name} &\n")
        time.sleep(1.0)
        os.system(f"cat {target_filepath} | nc {self.targetIP} 31339 &")
        while True:
            if self.sendrecv('ps\n').find('31339') != -1:
                time.sleep(1.0)
            else:
                break
        print(f'[*] transfer {file_name} to guest:/opt complete!')

    def run_gdbserver(self, PID, PORT=5168):
        print('[+] gdbserver at %s:%d attach on %s' %(self.targetIP, PORT, PID))
        print('[+] run "target remote %s:%d" in host gdb-multiarch' %(self.targetIP, PORT))
        self.send('/firmadyne/gdbserver %s:%d --attach %s\n' %(self.targetIP, PORT, PID))


def signal_handler(sig, frame):
    return


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)

    if sys.version[:1] != '3':
        #check python version is 3.X.X
        print('error : python version should be 3.X.X')
        exit(-1)
    elif len(sys.argv) != 2:
        print('usage: %s [iid]' % sys.argv[0])
        exit(-1)
    elif not sys.argv[1].isnumeric():
        #check iid is number
        print('error : iid should be number')
        exit(-1)
    elif not os.path.isdir('./scratch/%s'%(sys.argv[1])):
        print('error : invaild iid.')
        exit(-1)

    #initialize helper
    fh = firmae_helper(int(sys.argv[1]))
    fh.show_info()
    fh.connect()

    def menu():
        print('******************************')
        print('|       myae Debugger        |')
        print('******************************')
        print('[ 1 ] 调试固件') #run gdbserver
        print('[ 2 ] 登录固件') #connect to shell
        print('[ 3 ] 抓包固件') #tcpdump
        print('[ 4 ] 文件传输') #file transfer
        print('[ 5 ] 退出调试') #exit
        #print('1. connect to socat')

    while True:
        menu()
        try:
            select = int(input(':> '))
        except KeyboardInterrupt:
            break
        except:
            print("incorrect selection")
            continue

        if select == 13851687968:
            fh.connect_socat()
        elif select == 2:
            fh.connect_shell()
        elif select == 3:
            fh.tcpdump()
        elif select == 1:
            fh.show_processlist()
            try:
                PID = input('[+] 输入待调试进程ID:')
            except KeyboardInterrupt:
                pass
            else:
                if PID not in fh.pids:
                    print("目标进程ID【%s】不存在!" %PID)
                    continue
                fh.run_gdbserver(PID)
        elif select == 4:
            target_filepath = input('[+] 输入待上传固件的全路径完整文件名: ')
            fh.file_transfer(target_filepath)
        elif select == 5:
            break
        else:
            print("选择序号无效【%s】" %select)
    print('调试完成\n')
