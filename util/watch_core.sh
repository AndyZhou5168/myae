#!/bin/bash

ulimit -c unlimited
sudo sysctl -w kernel.core_pattern=core.%e.%p

while (true); do
    for cfn in `sudo myfind / -type f -newermt "$(date +%Y-%m-%d)" -name "core.*.*" 2>/dev/null`; do
        echo -e "找到core文件=> $cfn"
        name1=`dirname "$cfn"`
        name2=`basename "$cfn"`
        progm=$(echo "$name2" | cut -d'.' -f2)
        cpid3=$(echo "$name2" | cut -d'.' -f3)

        temp="$name1/$progm"
        if [ ! -e "$temp" ]; then
            echo "$cfn=> not exist the executable file [$temp], and ignore"
            contine
        fi

        cd $name1
        echo -e "\nbt\ninf r\nq\n" | gdb "./$progm" "./$name2" | cat - | nc -w 5 "$1" 31339
        rm -fr $cfn
        echo -e "处理完成，删除core文件=> $cfn"
    done
    sleep 1.5
done
