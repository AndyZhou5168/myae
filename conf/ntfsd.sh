#!/bin/bash
set -e
set +x

function signal_handler() {
    exit_status=$?
    ntfsd_running=0
    echo -e "\nCaught signal，退出码：$exit_status"
}

sudo service nfs-kernel-server start
ntfsd_running=1
sleep 2
echo -e "\n进程号【$$】，ntfs service has start！"

trap 'signal_handler' INT QUIT TERM

while [ $ntfsd_running -eq 1 ]; do
    sleep 1.5
done

sudo service nfs-kernel-server stop
echo -e "ntfs service has stop！\n"
