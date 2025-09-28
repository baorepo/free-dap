#!/bin/bash

if [ $# -eq 0 ]; then
    echo "错误：请提供 Bootloader 文件路径作为参数。"
    echo "用法：$0 <bootloader_path>"
    exit 1
fi

BOOTLOADER_PATH=$1

dd if=/dev/zero of=xiao_samd11.bin bs=1 count=$((0x1500))

dd if="$BOOTLOADER_PATH" of=xiao_samd11.bin conv=notrunc

dd if=../../platform/samd11/make/build/free_dap_d11_bl_5k.bin of=xiao_samd11.bin bs=1 seek=$((0x1500)) conv=notrunc

