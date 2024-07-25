#!/bin/bash
clear
echo -n "" > /proc/$$/fd/1
echo -e "固件蹦床系统启动，进程号【$PPID - $$】，时间【`date -d today +'%Y-%m-%d %H:%M:%S.%3N'`】"
echo -e "PLS选择固件及模式准备运行...\n"

function print_usage() {
    echo "Usage: ${0} [mode]... [brand] [firmware|firmware_directory]"
    echo "mode: use one option at once"
    echo "  -r, --run     : 运行模式"
    #echo " -r, --run     : run mode         - run emulation (no quit)"

    echo "  -t, --tri     : 蹦床模式"
    #echo " -c, --check   : check mode       - check network reachable and web access (quit)"

    #echo " -a, --analyze : analyze mode     - analyze vulnerability (quit)"
    #echo " -d, --debug   : debug mode       - debugging emulation (no quit)"
    #echo " -b, --boot    : boot debug mode  - kernel boot debugging using QEMU (no quit)"
}

function select_mode() {
    FIRMWARE_LIST=([0]="NV")
    for i in `ls ./firmwares/|grep -v README.md`; do
        FIRMWARE_LIST+=("$i")
    done

    MODE_LIST=(
        [0]="NV"
        [1]="[ 1 ] 蹦床模式"
        [2]="[ 2 ] 运行模式"
        [3]="[ 3 ] 调试模式"
        [4]="[ 4 ] 内核HOLD"
    )
    MODE_EXEC=([0]="NV" [1]="-t" [2]="-r" [3]="-d" [4]="-b")

    echo -e "目前支持的固件列表："
    local tmp=${#FIRMWARE_LIST[@]}
    tmp=`expr $tmp - 1`
    for i in $(seq 1 $tmp); do
        echo -e "\t[ $i ] ${FIRMWARE_LIST[i]}"
    done
    echo -e "PLS选择相应的序号"
    typeset -u U_FIRM_SELECT
    read -t 300 -p "您的" U_FIRM_SELECT
    if [[ "$U_FIRM_SELECT" =~ ^[1-$tmp]$ ]]; then
        FIRM_SELECT=$U_FIRM_SELECT
        FIRM_SELECT=${FIRMWARE_LIST[$FIRM_SELECT]}
        echo "选择的固件=> $FIRM_SELECT"
    else
        echo "无效输入：$FIRM_SELECT"
        exit 1
    fi

    echo -e "\n目前支持的模式列表："
    tmp=${#MODE_LIST[@]}
    tmp=`expr $tmp - 1`
    for i in $(seq 1 $tmp); do
        echo -e "\t${MODE_LIST[i]}"
    done
    echo -e "PLS选择相应的序号"
    typeset -u U_MODE_SELECT
    read -t 300 -p "您的" U_MODE_SELECT
    if [[ "$U_MODE_SELECT" =~ ^[1-$tmp]$ ]]; then
        MODE_SELECT=$U_MODE_SELECT
        local TMP="${MODE_LIST[$MODE_SELECT]%%模式*}"
        echo -e "选择的模式=> ${TMP:5}\n"
        MODE_SELECT="${MODE_EXEC[$MODE_SELECT]}"
    else
        echo "无效输入：$MODE_SELECT"
        exit 1
    fi
}

cd /opt/myae
if [ $# -ne 3 ]; then
    #print_usage ${0}
    select_mode
else
    echo -e "输入参数: 【$@】\n"
fi

set -e
set -u
set +x
source ./myae.config
reg_engine_toweb $PPID

function get_option() {
    OPTION=${1}

    if [ ${OPTION} = "-t" ] || [ ${OPTION} = "--tri" ]; then
        echo "check"
    elif [ ${OPTION} = "-c" ] || [ ${OPTION} = "--check" ]; then
        echo "check"
    elif [ ${OPTION} = "-a" ] || [ ${OPTION} = "--analyze" ]; then
        echo "analyze"
    elif [ ${OPTION} = "-r" ] || [ ${OPTION} = "--run" ]; then
        echo "run"
    elif [ ${OPTION} = "-d" ] || [ ${OPTION} = "--debug" ]; then
        echo "debug"
    elif [ ${OPTION} = "-b" ] || [ ${OPTION} = "--boot" ]; then
        echo "boot"
    else
        echo "none"
    fi
}

function get_brand() {
    INFILE=${1}
    BRAND=${2}
    if [ ${BRAND} = "auto" ]; then
        echo `./scripts/util.py get_brand ${INFILE} ${PSQL_IP}`
    else
        echo ${2}
    fi
}

if [ $# -eq 3 ]; then
    OPTION=`get_option ${1}`
else
    OPTION=`get_option ${MODE_SELECT}`
fi
if [ ${OPTION} == "none" ]; then
    #print_usage ${0}
    echo "模式选项错误"
    exit 1
fi

if (! id | egrep -sqi "root"); then
    echo -e "[\033[31m-\033[0m] This script must run with 'root' privilege"
    exit 1
fi

FIRMWARE="./firmwares/$FIRM_SELECT"
BRAND=`get_brand_fromweb ${FIRM_SELECT}`
if [ $# -eq 3 ]; then
    BRAND=${2}
fi
WORK_DIR=""
IID=-1

function run_emulation() {
    echo "固件【${1}】模拟开始..."
    if [ -f "/var/tmp/ae-lock" ]; then
        echo "固件模拟其他进程运行中，禁止多开!!!"
        return
    else
        touch /var/tmp/ae-lock
    fi

    INFILE=${1}
    BRAND=`get_brand ${INFILE} ${BRAND}`
    FILENAME=`basename ${INFILE%.*}`
    PING_RESULT=false
    WEB_RESULT=false
    IP=''

    if [ "${BRAND}" = "auto" ]; then
        echo -e "[\033[31m-\033[0m] Invalid brand ${INFILE}"
        return
    fi

    if [ -n "${FIRMAE_DOCKER-}" ]; then
        if ( ! ./scripts/util.py check_connection _ $PSQL_IP ); then
            echo -e "[\033[31m-\033[0m] docker container failed to connect to the hosts' postgresql!"
            return
        fi
    fi

    # Omit the argument '-b' when $BRAND is empty.
    [ -n "$BRAND" ] && brand_arg="-b $BRAND" || brand_arg=""

    # ================================
    # extract filesystem from firmware
    # ================================
    t_start="$(date -u +%s.%N)"

    # If the brand is not specified in the argument,
    # it will be inferred automatically from the path of the image file.
    timeout --preserve-status --signal SIGINT 300 \
        ./sources/extractor/extractor.py $brand_arg -sql $PSQL_IP -np \
        -nk $INFILE images 2>&1

    IID=`./scripts/util.py get_iid $INFILE $PSQL_IP`
    if [ ! "${IID}" ]; then
        echo -e "[\033[31m-\033[0m] extractor.py failed!"
        return
    fi

    # ================================
    # extract kernel from firmware
    # ================================
    # If the brand is not specified in the argument,
    # it will be inferred automatically from the path of the image file.
    timeout --preserve-status --signal SIGINT 300 \
        ./sources/extractor/extractor.py $brand_arg -sql $PSQL_IP -np \
        -nf $INFILE images 2>&1

    WORK_DIR=`get_scratch ${IID}`
    mkdir -p ${WORK_DIR}
    chmod a+rwx "${WORK_DIR}"
    chown -R "${USER}" "${WORK_DIR}"
    chgrp -R "${USER}" "${WORK_DIR}"
    echo $FILENAME > ${WORK_DIR}/name
    echo $BRAND > ${WORK_DIR}/brand
    sync

    if [ ${OPTION} = "check" ] && [ -e ${WORK_DIR}/result ]; then
        if (egrep -sqi "true" ${WORK_DIR}/result); then
            RESULT=`cat ${WORK_DIR}/result`
            return
        fi
        rm ${WORK_DIR}/result
    fi

    if [ ! -e ./images/$IID.tar.gz ]; then
        echo -e "[\033[31m-\033[0m] Extracting root filesystem failed!"
        echo "extraction failed" > ${WORK_DIR}/result
        return
    fi

    t_end="$(date -u +%s.%N)"
    time_extract="$(bc <<<"$t_end-$t_start")"
    echo $time_extract > ${WORK_DIR}/time_extract
    printf "固件提取完成，用时：%.3f（秒）" "$time_extract"

    echo -e "\n固件架构检测..."
    t_start="$(date -u +%s.%N)"
    ARCH=`./scripts/getArch.py ./images/$IID.tar.gz $PSQL_IP`
    echo "${ARCH}" > "${WORK_DIR}/architecture"

    if [ -e ./images/${IID}.kernel ]; then
        ./scripts/inferKernel.py ${IID}
    fi

    if [ ! "${ARCH}" ]; then
        echo -e "[\033[31m-\033[0m] Get architecture failed!"
        echo "get architecture failed" > ${WORK_DIR}/result
        return
    fi
    if ( check_arch ${ARCH} == 0 ); then
        echo -e "[\033[31m-\033[0m] Unknown architecture! - ${ARCH}"
        echo "Invalid architecture : ${ARCH}" > ${WORK_DIR}/result
        return
    fi

    t_end="$(date -u +%s.%N)"
    time_arch="$(bc <<<"$t_end-$t_start")"
    echo $time_arch > ${WORK_DIR}/time_arch
    printf "架构检测完成，用时：%.3f（秒）" "$time_arch"

    if (! egrep -sqi "true" ${WORK_DIR}/web); then
        echo -e "\n制作QEMU镜像..."
        get_qemu_ver `get_qemu ${ARCH}`

        t_start="$(date -u +%s.%N)"
        ./scripts/tar2db.py -i $IID -f ./images/$IID.tar.gz -h $PSQL_IP 2>&1 > ${WORK_DIR}/tar2db.log
        t_end="$(date -u +%s.%N)"
        time_tar="$(bc <<<"$t_end-$t_start")"
        echo $time_tar > ${WORK_DIR}/time_tar

        t_start="$(date -u +%s.%N)"
        ./scripts/makeImage.sh $IID $ARCH $FILENAME 2>&1 > ${WORK_DIR}/makeImage.log
        t_end="$(date -u +%s.%N)"
        time_image="$(bc <<<"$t_end-$t_start")"
        echo $time_image > ${WORK_DIR}/time_image
        printf "制作QEMU镜像完成，用时：%.3f（秒）" "`echo "$time_tar + $time_image"|bc`"

        echo -e "\n固件尝试模拟..."
        t_start="$(date -u +%s.%N)"
        # TIMEOUT is set in "myae.config" and the TIMEOUT is used for initial log collection.
        TIMEOUT=$TIMEOUT FIRMAE_NET=${FIRMAE_NET} \
            ./scripts/makeNetwork.py -i $IID -q -o -a ${ARCH} &> ${WORK_DIR}/makeNetwork.log
        ln -s ./run.sh ${WORK_DIR}/run_debug.sh | true
        ln -s ./run.sh ${WORK_DIR}/run_analyze.sh | true
        ln -s ./run.sh ${WORK_DIR}/run_boot.sh | true

        t_end="$(date -u +%s.%N)"
        time_network="$(bc <<<"$t_end-$t_start")"
        echo $time_network > ${WORK_DIR}/time_network
        printf "固件模拟完成，用时：%.3f（秒）" "$time_network"
    else
        echo -e "固件【${INFILE}】以前已成功模拟"
    fi

    if (egrep -sqi "true" ${WORK_DIR}/ping); then
        PING_RESULT=true
        IP=`cat ${WORK_DIR}/ip`
    fi
    if (egrep -sqi "true" ${WORK_DIR}/web); then
        WEB_RESULT=true
    fi

    echo -e "\n[固件身份ID] ${IID}\n[\033[33mMODE\033[0m] ${OPTION}"
    if ($PING_RESULT); then
        echo -e "[\033[32m+\033[0m] Network reachable on ${IP}!"
    fi
    if ($WEB_RESULT); then
        echo -e "[\033[32m+\033[0m] Web service on ${IP}"
        echo true > ${WORK_DIR}/result
        echo -e "固件尝试模拟成功\n"
    else
        echo false > ${WORK_DIR}/result
    fi
    rm -fr /var/tmp/ae-lock

    if [ ${OPTION} = "analyze" ]; then
        # 分析挖漏
        t_start="$(date -u +%s.%N)"
        if ($WEB_RESULT); then
            echo -e "\n等待Web服务启动..."
            ${WORK_DIR}/run_analyze.sh &
            IP=`cat ${WORK_DIR}/ip`
            check_network ${IP} false true

            echo -e "[\033[32m+\033[0m] start pentest!"
            cd analyses
            ./analyses_all.sh $IID $BRAND $IP $PSQL_IP
            cd -

            sync
            kill $(ps aux | grep `get_qemu ${ARCH}` | awk '{print $2}') 2> "${WORK_DIR}/kill-qemu.log"
            wait_sometime 2
        else
            echo -e "[\033[31m-\033[0m] Web unreachable"
        fi
        t_end="$(date -u +%s.%N)"
        time_analyze="$(bc <<<"$t_end-$t_start")"
        echo $time_analyze > ${WORK_DIR}/time_analyze

    elif [ ${OPTION} = "debug" ]; then
        # 调试模式
        if ($PING_RESULT); then
            echo -e "[\033[32m+\033[0m] 进入调试模式"
            IP=`cat ${WORK_DIR}/ip`
            ./scratch/$IID/run_debug.sh &

            check_network ${IP} true true
            ./debug.py ${IID}

            sync
            kill $(ps aux | grep `get_qemu ${ARCH}` | awk '{print $2}') 2> "${WORK_DIR}/kill-qemu.log" | true
            wait_sometime 2
        else
            echo -e "[\033[31m-\033[0m] Network unreachable"
        fi

    elif [ ${OPTION} = "run" ]; then
        # 运行模式
        echo -e "[\033[32m+\033[0m] 进入运行模式"
        check_network ${IP} false true &
        ${WORK_DIR}/run.sh

    elif [ ${OPTION} = "boot" ]; then
        # 内核HOLD
        echo -e "[\033[32m+\033[0m] 进入内核HOLD模式"
        if [ ! -d "/home/andy/myae/binaries" ]; then
            mkdir -p -m 777 /home/andy/myae/binaries
            mount --bind /opt/myae/binaries /home/andy/myae/binaries
        fi
        BOOT_KERNEL_PATH=`get_boot_kernel ${ARCH} true`
        BOOT_KERNEL=./binaries/`basename ${BOOT_KERNEL_PATH}`
        echo -e "BOOT_KERNEL=> 【$BOOT_KERNEL】"
        echo -e "[\033[32m+\033[0m] Connect with=> gdb-multiarch -q ${BOOT_KERNEL} -ex='target remote :1234'"
        ${WORK_DIR}/run_boot.sh
    fi

    echo "=====执行完成====="
    rm -fr "/var/tmp/f8fe6ef5.sh"
}

if [ $# -eq 3 ]; then
    FIRMWARE=${3}
fi

if [ ${OPTION} = "debug" ] && [ -d ${FIRMWARE} ]; then
    echo -e "[\033[31m-\033[0m] select firmware file on debug mode!"
    exit 1
fi

if [ ! -d ${FIRMWARE} ]; then
    run_emulation ${FIRMWARE}
else
    FIRMWARES=`find ${3} -type f`

    for FIRMWARE in ${FIRMWARES}; do
        if [ ! -d "${FIRMWARE}" ]; then
            run_emulation ${FIRMWARE}
        fi
    done
fi
