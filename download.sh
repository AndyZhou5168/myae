#!/bin/sh

set -e

download(){
 wget -N --continue -P./binaries/ $*
}

echo -e "Downloading binaries...\n"

echo -e "Downloading kernel 2.6 (MIPS)...\n"
download https://github.com/pr0v3rbs/FirmAE_kernel-v2.6/releases/download/v1.0/vmlinux.mipsel.2
download https://github.com/pr0v3rbs/FirmAE_kernel-v2.6/releases/download/v1.0/vmlinux.mipseb.2

echo -e "Downloading kernel 4.1 (MIPS)...\n"
download https://github.com/pr0v3rbs/FirmAE_kernel-v4.1/releases/download/v1.0/vmlinux.mipsel.4
download https://github.com/pr0v3rbs/FirmAE_kernel-v4.1/releases/download/v1.0/vmlinux.mipseb.4

echo -e "Downloading kernel 4.1 (ARM)...\n"
download https://github.com/pr0v3rbs/FirmAE_kernel-v4.1/releases/download/v1.0/zImage.armel
download https://github.com/pr0v3rbs/FirmAE_kernel-v4.1/releases/download/v1.0/vmlinux.armel

echo -e "Downloading busybox...\n"
download https://github.com/pr0v3rbs/FirmAE/releases/download/v1.0/busybox.armel
download https://github.com/pr0v3rbs/FirmAE/releases/download/v1.0/busybox.mipseb
download https://github.com/pr0v3rbs/FirmAE/releases/download/v1.0/busybox.mipsel

echo -e "Downloading console...\n"
download https://github.com/pr0v3rbs/FirmAE/releases/download/v1.0/console.armel
download https://github.com/pr0v3rbs/FirmAE/releases/download/v1.0/console.mipseb
download https://github.com/pr0v3rbs/FirmAE/releases/download/v1.0/console.mipsel

echo -e "Downloading libnvram...\n"
download https://github.com/pr0v3rbs/FirmAE/releases/download/v1.0/libnvram.so.armel
download https://github.com/pr0v3rbs/FirmAE/releases/download/v1.0/libnvram.so.mipseb
download https://github.com/pr0v3rbs/FirmAE/releases/download/v1.0/libnvram.so.mipsel
download https://github.com/pr0v3rbs/FirmAE/releases/download/v1.0/libnvram_ioctl.so.armel
download https://github.com/pr0v3rbs/FirmAE/releases/download/v1.0/libnvram_ioctl.so.mipseb
download https://github.com/pr0v3rbs/FirmAE/releases/download/v1.0/libnvram_ioctl.so.mipsel

echo -e "Downloading gdb...\n"
download https://github.com/pr0v3rbs/FirmAE/releases/download/v1.0/gdb.armel
download https://github.com/pr0v3rbs/FirmAE/releases/download/v1.0/gdb.mipseb
download https://github.com/pr0v3rbs/FirmAE/releases/download/v1.0/gdb.mipsel

echo -e "Downloading gdbserver...\n"
download https://github.com/pr0v3rbs/FirmAE/releases/download/v1.0/gdbserver.armel
download https://github.com/pr0v3rbs/FirmAE/releases/download/v1.0/gdbserver.mipseb
download https://github.com/pr0v3rbs/FirmAE/releases/download/v1.0/gdbserver.mipsel

echo -e "Downloading strace...\n"
download https://github.com/pr0v3rbs/FirmAE/releases/download/v1.0/strace.armel
download https://github.com/pr0v3rbs/FirmAE/releases/download/v1.0/strace.mipseb
download https://github.com/pr0v3rbs/FirmAE/releases/download/v1.0/strace.mipsel

echo "Done!"
