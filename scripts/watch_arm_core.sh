#!/firmadyne/sh

BUSYBOX=/firmadyne/busybox
HOST_IP="192.168.0.2"
echo -e `${BUSYBOX} date +'%Y-%m-%d %H:%M:%S'`": $0 begin running..."

ulimit -c unlimited
sysctl -w kernel.core_pattern=core.%e.%p

while (true); do
    for cfn in `${BUSYBOX} find / -type f -name "core.*.*" 2>/dev/null`; do
        echo -e "found core file=> $cfn"
        name1=`${BUSYBOX} dirname "$cfn"`
        name2=`${BUSYBOX} basename "$cfn"`
        progm=`echo "$name2" | ${BUSYBOX} awk -F'.' '{print $2}'`
        cpid3=`echo "$name2" | ${BUSYBOX} awk -F'.' '{print $3}'`
        temp="$name1/$progm"

        echo -e "progm=> $progm"
        echo -e "cpid3=> $cpid3"
        echo -e "temp=>  $temp"

        if [ ! -e "$temp" ]; then
            echo "$cfn=> not exist the executable file [$temp], and ignore"
            contine
        fi

        echo -e "\nbt\ninf r\nq\n" | /firmadyne/gdb "$temp" "$cfn" | ${BUSYBOX} cat - | ${BUSYBOX} nc -w 5 "$HOST_IP" 31339
        rm -fr $cfn
        echo -e "done core file and deleted=> $cfn"
    done
    ${BUSYBOX} sleep 1.5
done
