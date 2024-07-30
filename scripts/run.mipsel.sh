#!/bin/bash

set -e
set -u

if [ -e ./myae.config ]; then
    source ./myae.config
elif [ -e ../myae.config ]; then
    source ../myae.config
else
    echo "Error: not found 'myae.config'!!!"
    exit 1
fi

if check_number $1; then
    echo "Usage: run.mipsel.sh <image ID>"
    exit 1
fi
IID=${1}; add_cpenv IID
QEMU_INIT=${2}; add_cpenv QEMU_INIT

WORK_DIR=`get_scratch ${IID}`; add_cpenv WORK_DIR
IMAGE=`get_fs ${IID}`; add_cpenv IMAGE
KERNEL=`get_kernel "mipsel" false`; add_cpenv KERNEL
QEMU_MACHINE=`get_qemu_machine "mipsel"`; add_cpenv QEMU_MACHINE
QEMU_ROOTFS=`get_qemu_disk "mipsel"`; add_cpenv QEMU_ROOTFS

if (${FIRMAE_NET}); then
    QEMU_NETWORK="-device e1000,netdev=net0 -netdev user,id=net0 -device e1000,netdev=net1 -netdev user,id=net1 -device e1000,netdev=net2 -netdev user,id=net2 -device e1000,netdev=net3 -netdev user,id=net3"
else
    QEMU_NETWORK="-device e1000,netdev=net0 -netdev socket,id=net0,listen=:2000 -device e1000,netdev=net1 -netdev socket,id=net1,listen=:2001 -device e1000,netdev=net2 -netdev socket,id=net2,listen=:2002 -device e1000,netdev=net3 -netdev socket,id=net3,listen=:2003"
fi
add_cpenv QEMU_NETWORK

export BB_DISTANCE_ENV_VAR=/tmp/bxk_fuzz/distances.txt; add_cpenv BB_DISTANCE_ENV_VAR
export TARGETS_ENV_VAR=/tmp/bxk_fuzz/httpd.tgt; add_cpenv TARGETS_ENV_VAR
export UAF_ENV_VAR=/tmp/bxk_fuzz/httpd.tgt_uaf; add_cpenv UAF_ENV_VAR

print_cpenv
qemu-system-mipsel -m 256 -M ${QEMU_MACHINE} -kernel ${KERNEL} \
-drive if=ide,format=raw,file=${IMAGE} \
-append "firmadyne.syscall=1 "\
"root=${QEMU_ROOTFS} "\
"console=ttyS0 "\
"nandsim.parts=64,64,64,64,64,64,64,64,64,64 "\
"${QEMU_INIT} rw debug ignore_loglevel "\
"print-fatal-signals=1 "\
"FIRMAE_NET=${FIRMAE_NET} "\
"FIRMAE_NVRAM=${FIRMAE_NVRAM} "\
"FIRMAE_KERNEL=${FIRMAE_KERNEL} "\
"FIRMAE_ETC=${FIRMAE_ETC} "\
"user_debug=31" \
-serial file:${WORK_DIR}/qemu.initial.serial.log \
-serial unix:/tmp/qemu.${IID}.S1,server,nowait \
-monitor unix:/tmp/qemu.${IID},server,nowait \
-d unimp,guest_errors \
-display none ${QEMU_NETWORK}
